# Sync Monunhh/Super-ask from Bunkheang-heng/SuperAskAi.
# First run: mirrors Bunkheang's main into this repo and re-adds the report
# documents on top. Later runs: pulls anything new from Bunkheang's repo and
# pushes it here, keeping Monunhh/Super-ask the latest version of everything.
#
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File scripts/sync-from-bunkheang.ps1
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")

function Invoke-Git {
  # git writes progress to stderr; run through cmd so PowerShell 5.1 does not
  # wrap it in error records, and fail loudly on a real nonzero exit code.
  param([string]$GitCommand)
  cmd /c "git $GitCommand 2>&1"
  if ($LASTEXITCODE -ne 0) { throw "git $GitCommand failed (exit $LASTEXITCODE)" }
}

# Course material that lives in THIS repo (not in Bunkheang's) and must survive
# every sync. All report deliverables sit under docs/reports and the diagram
# sources under docs/report2-diagrams, so "docs" covers them.
$keep = @(
  "docs",
  "scripts/sync-from-bunkheang.ps1"
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
  if (Test-Path $item) {
    $dest = Join-Path $tmp $item
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    Copy-Item $item $dest -Recurse -Force
  }
}

# Point main at Bunkheang's latest.
Invoke-Git "switch -C main bunkheang/main"

# Restore the report artifacts on top and commit them if anything changed.
foreach ($item in $keep) {
  $src = Join-Path $tmp $item
  if (Test-Path $src) {
    $parent = Split-Path $item
    if (-not $parent) { $parent = "." }
    New-Item -ItemType Directory -Force $parent | Out-Null
    Copy-Item $src $parent -Recurse -Force
  }
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
