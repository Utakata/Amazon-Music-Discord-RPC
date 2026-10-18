# Issue 52 Final Test Build

This is the final test build of Amazon Music RPC v5.0.4 for issue #52:
https://github.com/eripum9/Amazon-Music-Discord-RPC/issues/52

Test build ID: `issue52-3`. The app version is `5.0.4`; this is not a stable
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
   Get-FileHash .\AmazonMusicRPC_Setup_v5.0.4_issue52-final-test.exe -Algorithm SHA256
   ```

3. Quit Amazon Music RPC through its tray menu, then run
   `AmazonMusicRPC_Setup_v5.0.4_issue52-final-test.exe`. It updates the existing
   installation and keeps its settings.
4. Start RPC and use **Launch Amazon Music Now** as before. The console in
   Diagnostics will show `[Metadata owner]` entries with `issue52-3 backend=win32` when an
   owner query runs.

## Collect Reports

1. Before starting Helldivers 2, play a song and confirm that **Amazon Metadata**
   is working. Use **Diagnostics > Export Report** and label the ZIP `before`.
2. Start the game, reach gameplay, and keep it running for several minutes.
   Change tracks and seek within a song. Confirm enhanced metadata and timing
   remain available, then export a report labelled `during`. If fallback occurs,
   mention approximately when. Keep RPC and Amazon Music running.
3. Close the game and export a report labelled `after`. If metadata switched
   to fallback, wait about one minute and mention whether it recovered.
4. Attach all three reports to issue #52. Mention approximately when the game
   entered gameplay and when it closed, and explicitly confirm whether the
   final v5.0.4 build works. The fix will only be merged after confirmation
   and successful pull-request checks.

The reports include the native owner-query outcome, duration, Windows error
code, and bounded error text. They do not collect a full list of running processes.

## Return to the Stable Build

Quit RPC and reinstall v5.0.3 from:
https://github.com/eripum9/Amazon-Music-Discord-RPC/releases/tag/v5.0.3

The Actions artifact expires after 30 days. `build-info.json` records the exact
source commit, workflow run, and installer checksum.
