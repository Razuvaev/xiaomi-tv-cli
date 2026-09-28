from pathlib import Path

from tvctl import adb, report


def test_create_report(tmp_path: Path, monkeypatch) -> None:
    properties = {
        "ro.product.manufacturer": "Haier",
        "ro.product.brand": "Haier",
        "ro.product.model": "Test TV",
        "ro.product.device": "test_device",
        "ro.product.name": "test_product",
        "ro.product.board": "test_board",
        "ro.build.version.release": "11",
        "ro.build.version.sdk": "30",
        "ro.build.display.id": "TEST_BUILD",
        "ro.build.fingerprint": "Haier/test/test:11/TEST/1:user/release-keys",
    }

    monkeypatch.setattr(adb, "get_property", lambda name: properties.get(name, ""))
    monkeypatch.setattr(adb, "get_home_launcher", lambda: "com.google.android.tvlauncher/.MainActivity")

    def fake_shell(*arguments: str, timeout: int = 30):
        if arguments[-1:] == ("-d",):
            output = "package:com.example.disabled\n"
        elif arguments[-1:] == ("-s",):
            output = "package:com.android.system\n"
        elif arguments[-1:] == ("-3",):
            output = "package:com.example.app\n"
        else:
            output = "package:com.android.system\npackage:com.example.app\npackage:com.example.disabled\n"

        return adb.ADBResult(return_code=0, stdout=output, stderr="")

    monkeypatch.setattr(adb, "shell", fake_shell)

    output = tmp_path / "report.txt"
    result = report.create_report(output)
    content = output.read_text(encoding="utf-8")

    assert result == output
    assert "Manufacturer: Haier" in content
    assert "Model: Test TV" in content
    assert "Android: 11" in content
    assert "Home launcher: com.google.android.tvlauncher/.MainActivity" in content
    assert "=== Installed packages (3) ===" in content
    assert "=== Disabled packages (1) ===" in content
    assert "=== System packages (1) ===" in content
    assert "=== Third-party packages (1) ===" in content
    assert "com.example.disabled" in content
