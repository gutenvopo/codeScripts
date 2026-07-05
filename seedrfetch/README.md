# SeedrFetch

SeedrFetch is a futuristic dark-mode Windows desktop client for Seedr Premium. Paste a magnet or `.torrent` URL, let Seedr fetch it in the cloud, then download the finished files or folders to your PC.

## Install and run

Requires Python 3.13 on Windows 11.

```powershell
..\rwakiDev_v3\Scripts\python.exe -m pip install -r requirements.txt
..\rwakiDev_v3\Scripts\python.exe main.py
```

The workspace's VS Code interpreter and launch profiles are configured for
`rwakiDev_v3`. When that environment exists beside the `seedrfetch` folder,
`main.py` also relaunches itself with it if invoked through another Python.

## Verify your install

Run the logging repro check after installing dependencies. It deliberately uses invalid credentials, verifies the translated error, and confirms that the main, HTTP, and TLS logs all contain evidence from the operation.

```powershell
..\rwakiDev_v3\Scripts\python.exe scripts\log_smoke_test.py
```

## Getting started

1. Sign in with the same email and password used at seedr.cc, or choose Device Code and authorize at `https://www.seedr.cc/devices`.
2. Paste a `magnet:?xt=urn:btih:...` link or an HTTPS `.torrent` URL into the dashboard.
3. Choose **Add to Seedr** and wait for the cloud transfer to finish.
4. Right-click a finished file or folder and choose **Download here**.
5. Use **Change...** beside the destination to select another local folder.

Partial downloads use a `.part` file and resume with HTTP Range requests. The file is renamed when complete.

## Managing storage and accounts

The footer displays Seedr storage usage when the API supplies it. Right-click cloud items to delete them. To change authentication methods, sign out under Settings and use the other login tab.

## Norton / antivirus users

SeedrFetch injects `truststore` before importing Requests, so it uses the Windows certificate store. This normally handles Norton, Kaspersky, corporate proxies, and other HTTPS-inspection products automatically.

If secure connections still fail, open **Settings > Run Diagnostics**. You can select a custom PEM CA bundle or add `*.seedr.cc` as an exception in the antivirus HTTPS-scanning settings. Disabling SSL verification is insecure and is provided only as a temporary diagnostic.

## Troubleshooting

**Can't sign in:** Check the email and password, try Device Code, then run Diagnostics.

**Downloads are slow or stall:** HTTPS inspection can reset TLS connections. Add the Seedr exception in the security product and retry; the `.part` file will be resumed.

**Logs:** `%USERPROFILE%\.seedrfetch\logs\`. Main, HTTP, and TLS logs rotate at 2 MB with five backups. Uncaught exceptions create snapshots under `%USERPROFILE%\.seedrfetch\crashes\`, and credential-like values are redacted before formatting.

## Keyboard shortcuts

- `Ctrl+L`: focus the add-link field
- `F5`: refresh the drive
- `Ctrl+,`: open Settings
- `F1`: open Help

SeedrFetch 1.0.0 is an independent client and does not provide playback, WebDAV, FTP, tray integration, or automatic updates.

## Project memory

Development decisions and agent instructions live in [AGENTS.md](../AGENTS.md).
All notable changes are recorded in [CHANGELOG.md](../CHANGELOG.md).

## Development setup

Install the development hook runner and enable the repository hooks:

```powershell
python -m pip install pre-commit
pre-commit install
```

The hooks require a `CHANGELOG.md` entry for Python changes and verify that
`seedrfetch/requirements.txt` covers every imported third-party package.
