# Issue 52 Test Build 2

This is a test build of Amazon Music RPC v5.0.3 for issue #52:
https://github.com/eripum9/Amazon-Music-Discord-RPC/issues/52

Test build ID: `issue52-2`. The app version remains `5.0.3`; this is not a stable
release. It replaces the recurring PowerShell/CIM listener-owner query with
native Windows TCP-table and executable-image queries. It verifies the actual
listening process and rechecks ownership before accepting the result. Unknown,
inaccessible, or changed owners still cause a safe fallback. Testing with
Helldivers 2 is needed to confirm the reported problem is resolved.

## Install

1. Download the artifact ZIP from the linked GitHub Actions run while signed in
   to GitHub, then extract it.
2. Check the installer SHA256 against the accompanying `.exe.sha256` file. In
   PowerShell, run:

   ```powershell
   Get-FileHash .\AmazonMusicRPC_Setup_v5.0.3_issue52-test-2.exe -Algorithm SHA256
   ```

3. Quit Amazon Music RPC through its tray menu, then run
   `AmazonMusicRPC_Setup_v5.0.3_issue52-test-2.exe`. It updates the existing
   installation and keeps its settings.
4. Start RPC and use **Launch Amazon Music Now** as before. The console in
   Diagnostics will show `[Metadata owner]` entries with `issue52-2 backend=win32` when an
   owner query runs.

## Collect Reports

1. Before starting Helldivers 2, play a song and confirm that **Amazon Metadata**
   is working. Use **Diagnostics > Export Report** and label the ZIP `before`.
2. Start the game and reach the point where the metadata switches to fallback.
   Export another report labelled `during`. Keep RPC and Amazon Music running.
3. Close the game, wait for enhanced metadata to recover (or about one minute
   if it does not), and export a report labelled `after`.
4. Attach all three reports to issue #52. Mention approximately when the game
   entered gameplay and when it closed, and whether Amazon Music kept playing.

The reports include the native owner-query outcome, duration, Windows error
code, and bounded error text. They do not collect a full list of running processes.

## Return to the Stable Build

Quit RPC and reinstall v5.0.3 from:
https://github.com/eripum9/Amazon-Music-Discord-RPC/releases/tag/v5.0.3

The Actions artifact expires after 30 days. `build-info.json` records the exact
source commit, workflow run, and installer checksum.
