from __future__ import annotations

import ipaddress
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from tvctl import adb

DEFAULT_ADB_PORT = 5555
DEFAULT_TIMEOUT = 0.15
DEFAULT_WORKERS = 64


class DiscoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class DiscoveredDevice:
    ip_address: str
    port: int = DEFAULT_ADB_PORT
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    android_version: str = "Unknown"

    @property
    def target(self) -> str:
        return f"{self.ip_address}:{self.port}"


def get_local_ip_address() -> str:
    try:
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise DiscoveryError("Could not inspect network interfaces.") from error

    candidates: list[ipaddress.IPv4Address] = []

    for line in result.stdout.splitlines():
        stripped_line = line.strip()

        if not stripped_line.startswith("inet "):
            continue

        parts = stripped_line.split()

        if len(parts) < 2:
            continue

        try:
            address = ipaddress.ip_address(parts[1])
        except ValueError:
            continue

        if not isinstance(address, ipaddress.IPv4Address):
            continue

        if not address.is_private or address.is_loopback:
            continue

        if address in ipaddress.ip_network("198.18.0.0/15"):
            continue

        candidates.append(address)

    if not candidates:
        raise DiscoveryError("Could not find a local IPv4 address.")

    candidates.sort(
        key=lambda address: (
            not str(address).startswith("192.168."),
            not str(address).startswith("10."),
            int(address),
        )
    )

    return str(candidates[0])


def get_default_network() -> ipaddress.IPv4Network:
    local_ip = get_local_ip_address()

    try:
        return ipaddress.ip_network(f"{local_ip}/24", strict=False)
    except ValueError as error:
        raise DiscoveryError(f"Could not determine network for {local_ip}.") from error


def is_port_open(ip_address: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip_address, port), timeout=timeout):
            return True
    except OSError:
        return False


def discover(
    network: ipaddress.IPv4Network | None = None,
    port: int = DEFAULT_ADB_PORT,
    timeout: float = DEFAULT_TIMEOUT,
    workers: int = DEFAULT_WORKERS,
) -> tuple[DiscoveredDevice, ...]:
    selected_network = network or get_default_network()
    discovered_devices: list[DiscoveredDevice] = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(is_port_open, str(host), port, timeout): str(host)
            for host in selected_network.hosts()
        }

        for future in as_completed(futures):
            ip_address = futures[future]

            if future.result():
                discovered_devices.append(
                    DiscoveredDevice(
                        ip_address=ip_address,
                        port=port,
                    )
                )

    return tuple(
        sorted(
            discovered_devices,
            key=lambda device: ipaddress.ip_address(device.ip_address),
        )
    )

def get_device_property(target: str, property_name: str) -> str:
    result = adb.run("-s", target, "shell", "getprop", property_name, timeout=10)

    if result.return_code != 0:
        return "Unknown"

    return result.stdout.strip() or "Unknown"


def identify_device(device: DiscoveredDevice) -> DiscoveredDevice:
    connect_result = adb.connect(device.ip_address, device.port)
    output = connect_result.output.lower()

    if "connected to" not in output and "already connected" not in output:
        return device

    return DiscoveredDevice(
        ip_address=device.ip_address,
        port=device.port,
        manufacturer=get_device_property(device.target, "ro.product.manufacturer"),
        model=get_device_property(device.target, "ro.product.model"),
        android_version=get_device_property(device.target, "ro.build.version.release"),
    )


def identify_devices(
    devices: tuple[DiscoveredDevice, ...],
    workers: int = 8,
) -> tuple[DiscoveredDevice, ...]:
    identified_devices: list[DiscoveredDevice] = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(identify_device, device): device
            for device in devices
        }

        for future in as_completed(futures):
            identified_devices.append(future.result())

    return tuple(
        sorted(
            identified_devices,
            key=lambda device: ipaddress.ip_address(device.ip_address),
        )
    )    
