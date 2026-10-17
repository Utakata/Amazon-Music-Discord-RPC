# Issue 52 Diagnostic Build

This is a diagnostic build of Amazon Music RPC v5.0.3 for issue #52:
https://github.com/eripum9/Amazon-Music-Discord-RPC/issues/52

Diagnostic ID: `issue52-1`. The app version remains `5.0.3`; this is not a stable
release or a confirmed fix. It adds details about the Windows metadata
listener-owner query. Verification rules and fallback behavior remain enabled.

## Install

1. Download the artifact ZIP from the linked GitHub Actions run while signed in
   to GitHub, then extract it.
2. Check the installer SHA256 against the accompanying `.exe.sha256` file. In
   PowerShell, run:

   ```powershell
   Get-FileHash .\AmazonMusicRPC_Setup_v5.0.3_issue52-diagnostic-1.exe -Algorithm SHA256
   ```

3. Quit Amazon Music RPC through its tray menu, then run
   `AmazonMusicRPC_Setup_v5.0.3_issue52-diagnostic-1.exe`. It updates the existing
   installation and keeps its settings.
4. Start RPC and use **Launch Amazon Music Now** as before. The console in
   Diagnostics will show `[Metadata owner]` entries with `issue52-1` when an
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

The reports include the owner-query outcome, duration, error category, and
bounded error text. They do not collect a full list of running processes.

## Return to the Stable Build

Quit RPC and reinstall v5.0.3 from:
https://github.com/eripum9/Amazon-Music-Discord-RPC/releases/tag/v5.0.3

The Actions artifact expires after 30 days. `build-info.json` records the exact
source commit, workflow run, and installer checksum.
