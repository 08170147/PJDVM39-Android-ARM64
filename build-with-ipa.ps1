param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$IpaPath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ResolvedIpa = (Resolve-Path -LiteralPath $IpaPath).Path
Set-Location $Root

$Asset = Join-Path $Root "app/src/main/assets/pjdvm39/exitmenu_2048x2048.bc5"
$Report = Join-Path $Root "exitmenu-bc5-extract.json"
$Apk = Join-Path $Root "app/build/outputs/apk/debug/app-debug.apk"

Write-Host "[1/4] Extracting the real ExitMenu BC5 payload from IPA..."
python tools/extract_exitmenu_bc5_from_ipa.py $ResolvedIpa --out $Asset --report $Report
if ($LASTEXITCODE -ne 0) { throw "IPA extraction failed" }

Write-Host "[2/4] Verifying payload size and SHA-256..."
$AssetInfo = Get-Item -LiteralPath $Asset
if ($AssetInfo.Length -ne 4194304) { throw "Unexpected BC5 payload size: $($AssetInfo.Length)" }
$ReportJson = Get-Content -Raw -LiteralPath $Report | ConvertFrom-Json
$ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Asset).Hash.ToLowerInvariant()
if ($ActualHash -ne $ReportJson.payload_sha256) { throw "Extract report SHA-256 mismatch" }
Write-Host "Verified $($AssetInfo.Length) bytes; SHA-256 $ActualHash"

Write-Host "[3/4] Building ARM64 debug APK with the current repository shaders..."
gradle :app:assembleDebug
if ($LASTEXITCODE -ne 0) { throw "Gradle build failed" }
if (-not (Test-Path -LiteralPath $Apk)) { throw "APK was not produced: $Apk" }

Write-Host "[4/4] Verifying APK contains both real texture and compiled channel-split shader..."
$Entries = & jar tf $Apk
if ($LASTEXITCODE -ne 0) { throw "Could not inspect APK" }
if ($Entries -notcontains "assets/pjdvm39/exitmenu_2048x2048.bc5") { throw "Real ExitMenu asset is missing from APK" }
if ($Entries -notcontains "assets/pjdvm39/bc5_sample.frag.spv") { throw "Fragment SPIR-V is missing from APK" }

$Output = Join-Path $Root "PJDVM39-Android-ARM64-ExitMenu-ChannelSplit.apk"
Copy-Item -LiteralPath $Apk -Destination $Output -Force
Write-Host "PASS: combined real-asset + channel-split APK created:"
Write-Host $Output
