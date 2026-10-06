# Sync Monunhh/Super-ask from Bunkheang-heng/SuperAskAi.
# First run: mirrors Bunkheang's main into this repo and re-adds the report
# documents on top. Later runs: pulls anything new from Bunkheang's repo and
# pushes it here, keeping Monunhh/Super-ask the latest version of everything.
#
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File sync-from-bunkheang.ps1
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Invoke-Git {
  # git writes progress to stderr; run through cmd so PowerShell 5.1 does not
  # wrap it in error records, and fail loudly on a real nonzero exit code.
  param([string]$GitCommand)
  cmd /c "git $GitCommand 2>&1"
  if ($LASTEXITCODE -ne 0) { throw "git $GitCommand failed (exit $LASTEXITCODE)" }
}

# Report artifacts that live in THIS repo (not in Bunkheang's) and must survive
# every sync. Add new report files here as the course goes on.
$keep = @(
  "SuperAsk-3c-use-cases.html",
  "SuperAsk-report2-interaction-diagrams.html",
  "superask-use-case-diagram.png",
  "sync-from-bunkheang.ps1",
  "docs"
)

Invoke-Git "fetch bunkheang"
Invoke-Git "fetch origin"

# Safety net: keep a copy of whatever origin/main points at (ignore failure if
# the dated backup branch already exists).
$backup = "backup-$(Get-Date -Format 'yyyy-MM-dd')"
cmd /c "git push origin origin/main:refs/heads/$backup 2>&1"

# Stash the keep-list to a temp folder (they may be untracked or tracked).
$tmp = Join-Path $env:TEMP "superask-sync-$(Get-Random)"
New-Item -ItemType Directory -Force $tmp | Out-Null
foreach ($item in $keep) {
  if (Test-Path $item) { Copy-Item $item (Join-Path $tmp $item) -Recurse -Force }
}

# Point main at Bunkheang's latest.
Invoke-Git "switch -C main bunkheang/main"

# Restore the report artifacts on top and commit them if anything changed.
foreach ($item in $keep) {
  $src = Join-Path $tmp $item
  if (Test-Path $src) { Copy-Item $src . -Recurse -Force }
}
Invoke-Git "add -A"
$pending = git status --porcelain
if ($pending) {
  Invoke-Git "commit -m `"Add course report documents on top of the synced SuperAskAi code`""
}

# Publish. force-with-lease protects against clobbering pushes made elsewhere
# after this script's fetch.
Invoke-Git "push origin main --force-with-lease"

Remove-Item $tmp -Recurse -Force
Write-Host "Sync complete: Monunhh/Super-ask now matches Bunkheang-heng/SuperAskAi plus the report documents."
