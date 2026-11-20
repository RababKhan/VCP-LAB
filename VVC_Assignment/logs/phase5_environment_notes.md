# Phase 5 environment notes (Linux build via WSL2)

## 2026-11-04 19:45: WSL2 enablement (approved by the user)

Pre-install state (read-only checks):
- WSL not installed (`wsl --status`: "The Windows Subsystem for Linux is not installed").
- Windows 11 Home Single Language 10.0.26200, x64. CPU: Intel Core i7-1260P. VirtualizationFirmwareEnabled = True, SLAT = True, HypervisorPresent = False. RAM 15.7 GiB.
- Optional features: VirtualMachinePlatform = Disabled, Microsoft-Windows-Subsystem-Linux = Disabled, HypervisorPlatform = Disabled.
- Free disk: C: 113.9 GiB, D: 42.7 GiB, E: 111.3 GiB. No pending reboot. The session was not elevated.

User decisions: approve the install; keep the VHDX at the default location (C:).

Action: elevated (UAC) `wsl.exe --install --no-distribution`. Log: `logs/phase5_wsl_install_20261104_194528.log`.
- DISM enabled the feature: "The operation completed successfully". "Installing Windows optional component: VirtualMachinePlatform … Changes will not be effective until the system is rebooted."
- WSL package downloaded and installed: "Windows Subsystem for Linux 3.0.3 has been installed".
- The elevated process exited with code 1. The "Exit code" line that the wrapper should have appended is missing from the log, so the exact wsl.exe exit code was not captured. Interpretation: the operation reported success but requires a reboot.

Post-install state (verified):
- VirtualMachinePlatform: InstallState 1 (Enabled; takes effect after reboot).
- Microsoft-Windows-Subsystem-Linux (the legacy WSL1 feature): InstallState 2 (not enabled by this install; WSL2 via the WSL package needs only VirtualMachinePlatform).
- Appx package MicrosoftCorporationII.WindowsSubsystemForLinux 3.0.3.0; `C:\Program Files\WSL\wsl.exe` 3.0.3.0.
- CBS RebootPending: True. The computer was NOT restarted by Claude; the user restarts manually.

Consequence to record in the Phase 5 report: once VirtualMachinePlatform is active, Windows runs on top of the Hyper-V hypervisor. The completed Windows experiments (Phases 3, 4A, 4B and the supplementary run) were all measured before this change. Any later Windows timing would be under different conditions.

## Next steps (after the user's manual restart)
1. Verify `wsl --version` and `wsl --status`, and that HypervisorPresent = True.
2. `wsl --install -d Ubuntu-24.04`. The user creates the Linux username and password in the first-launch terminal.
3. Then Phase 5 Step 2 (apt dependencies as root via `wsl -u root`), Step 3 (clone the exact commits into ~/vvc_linux in the Linux filesystem), Step 4 (build and tests), Step 5 (16-frame smoke test against the Windows reference), and Step 6 (report).

## 2026-11-04 20:27: post-"restart" verification FAILED (user reported a restart)
- `wsl --version`: WSL 3.0.3.0, kernel 6.18.54.1-1, WSLg 1.0.79 (exit 0).
- `wsl --status`: "WSL2 is unable to start since virtualization is not enabled on this machine. Please ensure the "Virtual Machine Platform" optional component is enabled ..."
- `wsl -l -v`: no installed distributions.
- HypervisorPresent = False; VirtualMachinePlatform InstallState 1 (enabled, not yet active).
- Reboot still pending: CBS RebootPending = True, PendingFileRenameOperations present.
- System event log for today: the only boot-related events are at 09:36:12 (Kernel-Boot id 27 "boot type 0x1", which is a Fast Startup / hybrid boot, and Modern Standby enter/exit). There is no shutdown, restart or boot event after the WSL install at 19:45. Fast Startup is enabled (HiberbootEnabled = 1).
- Conclusion (measured): Windows has not restarted since the feature was enabled, so the pending change has not been applied. Ubuntu was NOT installed. Waiting for the user to perform a real Start > Power > Restart.

## 2026-11-04 22:06 to 2026-11-05 09:45: verification passed, Phase 5 completed
- Real restart at 2026-11-04 22:04:58 (boot type 0x0). HypervisorPresent=True, no reboot pending, wsl --status OK.
- Ubuntu-24.04 installed (WSL 2). The user created the default user vvcuser.
- Dependencies, build (0 warnings/0 errors), unit tests and 39/39 vvenc ctest tests all passed.
- Smoke test: Linux bitstream and recon are byte-identical to Windows (SHA256 5037d075...e1bb).
- Report: report/phase5_linux_build_report.md
