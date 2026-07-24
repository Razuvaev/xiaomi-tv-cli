from unittest.mock import patch

from tvctl import adb, packages


def test_get_state_returns_not_installed() -> None:
    with patch.object(packages, "is_installed", return_value=False):
        state = packages.get_state("com.example.missing")

    assert state == packages.PackageState(
        name="com.example.missing",
        installed=False,
        enabled=False,
    )


def test_get_state_returns_enabled_package() -> None:
    with (
        patch.object(packages, "is_installed", return_value=True),
        patch.object(packages, "is_disabled", return_value=False),
    ):
        state = packages.get_state("com.example.enabled")

    assert state == packages.PackageState(
        name="com.example.enabled",
        installed=True,
        enabled=True,
    )


def test_get_state_returns_disabled_package() -> None:
    with (
        patch.object(packages, "is_installed", return_value=True),
        patch.object(packages, "is_disabled", return_value=True),
    ):
        state = packages.get_state("com.example.disabled")

    assert state == packages.PackageState(
        name="com.example.disabled",
        installed=True,
        enabled=False,
    )


def test_is_installed_returns_true_when_pm_path_exists() -> None:
    result = adb.ADBResult(
        return_code=0,
        stdout="package:/system/app/Example/Example.apk",
        stderr="",
    )

    with patch.object(adb, "shell", return_value=result):
        assert packages.is_installed("com.example.app") is True


def test_is_installed_returns_false_for_missing_package() -> None:
    result = adb.ADBResult(
        return_code=1,
        stdout="",
        stderr="",
    )

    with patch.object(adb, "shell", return_value=result):
        assert packages.is_installed("com.example.missing") is False


def test_is_disabled_finds_exact_package() -> None:
    result = adb.ADBResult(
        return_code=0,
        stdout=(
            "package:com.example.first\n"
            "package:com.example.disabled\n"
            "package:com.example.last"
        ),
        stderr="",
    )

    with patch.object(adb, "shell", return_value=result):
        assert packages.is_disabled("com.example.disabled") is True
        assert packages.is_disabled("com.example") is False


def test_disable_runs_expected_adb_command() -> None:
    expected = adb.ADBResult(return_code=0, stdout="", stderr="")

    with patch.object(adb, "shell", return_value=expected) as shell_mock:
        result = packages.disable("com.example.app")

    shell_mock.assert_called_once_with(
        "pm",
        "disable-user",
        "--user",
        "0",
        "com.example.app",
    )
    assert result is expected


def test_enable_runs_expected_adb_command() -> None:
    expected = adb.ADBResult(return_code=0, stdout="", stderr="")

    with patch.object(adb, "shell", return_value=expected) as shell_mock:
        result = packages.enable("com.example.app")

    shell_mock.assert_called_once_with(
        "pm",
        "enable",
        "com.example.app",
    )
    assert result is expected
