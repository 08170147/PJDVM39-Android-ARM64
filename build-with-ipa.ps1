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
$GeneratedAssets = Join-Path $Root "app/build/generated/assets/pjdvm39"
$Apk = Join-Path $Root "app/build/outputs/apk/debug/app-debug.apk"

Write-Host "[1/5] Extracting the real ExitMenu BC5 payload from IPA..."
python tools/extract_exitmenu_bc5_from_ipa.py $ResolvedIpa --out $Asset --report $Report
if ($LASTEXITCODE -ne 0) { throw "IPA extraction failed" }

Write-Host "[2/5] Verifying payload size and SHA-256..."
$AssetInfo = Get-Item -LiteralPath $Asset
if ($AssetInfo.Length -ne 4194304) { throw "Unexpected BC5 payload size: $($AssetInfo.Length)" }
$ReportJson = Get-Content -Raw -LiteralPath $Report | ConvertFrom-Json
$ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Asset).Hash.ToLowerInvariant()
if ($ActualHash -ne $ReportJson.payload_sha256) { throw "Extract report SHA-256 mismatch" }
Write-Host "Verified $($AssetInfo.Length) bytes; SHA-256 $ActualHash"

Write-Host "[3/5] Compiling and validating the current repository shaders..."
$Glslang = Get-Command glslangValidator -ErrorAction SilentlyContinue
$SpirvVal = Get-Command spirv-val -ErrorAction SilentlyContinue
if (-not $Glslang) { throw "glslangValidator not found. Install the Vulkan SDK and add its Bin directory to PATH." }
if (-not $SpirvVal) { throw "spirv-val not found. Install the Vulkan SDK and add its Bin directory to PATH." }
New-Item -ItemType Directory -Force -Path $GeneratedAssets | Out-Null
& $Glslang.Source -V --target-env vulkan1.0 -S vert (Join-Path $Root "shaders/bc5_sample.vert") -o (Join-Path $GeneratedAssets "bc5_sample.vert.spv")
if ($LASTEXITCODE -ne 0) { throw "Vertex shader compilation failed" }
& $Glslang.Source -V --target-env vulkan1.0 -S frag (Join-Path $Root "shaders/bc5_sample.frag") -o (Join-Path $GeneratedAssets "bc5_sample.frag.spv")
if ($LASTEXITCODE -ne 0) { throw "Fragment shader compilation failed" }
& $SpirvVal.Source --target-env vulkan1.0 (Join-Path $GeneratedAssets "bc5_sample.vert.spv")
if ($LASTEXITCODE -ne 0) { throw "Vertex SPIR-V validation failed" }
& $SpirvVal.Source --target-env vulkan1.0 (Join-Path $GeneratedAssets "bc5_sample.frag.spv")
if ($LASTEXITCODE -ne 0) { throw "Fragment SPIR-V validation failed" }

Write-Host "[4/5] Building ARM64 debug APK..."
.\gradlew.bat :app:assembleDebug
if ($LASTEXITCODE -ne 0) { throw "Gradle build failed" }
if (-not (Test-Path -LiteralPath $Apk)) { throw "APK was not produced: $Apk" }

Write-Host "[5/5] Verifying APK contains real texture and current compiled shaders..."
$Entries = & jar tf $Apk
if ($LASTEXITCODE -ne 0) { throw "Could not inspect APK" }
$Required = @(
    "assets/pjdvm39/exitmenu_2048x2048.bc5",
    "assets/pjdvm39/bc5_sample.vert.spv",
    "assets/pjdvm39/bc5_sample.frag.spv"
)
foreach ($Entry in $Required) {
    if ($Entries -notcontains $Entry) { throw "Required APK asset is missing: $Entry" }
}

$Output = Join-Path $Root "PJDVM39-Android-ARM64-ExitMenu-ChannelSplit.apk"
Copy-Item -LiteralPath $Apk -Destination $Output -Force
Write-Host "PASS: combined real-asset + freshly compiled channel-split APK created:"
Write-Host $Output
