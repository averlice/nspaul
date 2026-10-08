# VW Paul synthesis harness - MUST run in 32-bit PowerShell (SysWOW64).
# Usage: powershell.exe -File synthesize.ps1 -ShardIndex 0 -ShardCount 4
param(
    [string]$PromptsFile = 'C:\paul\prompts.tsv',
    [string]$OutDir = 'C:\paul\wavs',
    [string]$ErrorLog = 'C:\paul\errors.log',
    [int]$ShardIndex = 0,
    [int]$ShardCount = 1
)

$ErrorActionPreference = 'Stop'

if ([Environment]::Is64BitProcess) {
    Write-Error "This script must run in 32-bit PowerShell. Launch via SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
    exit 10
}

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$voice = New-Object -ComObject SAPI.SpVoice
$voices = $voice.GetVoices()
$target = $null
for ($i = 0; $i -lt $voices.Count; $i++) {
    if ($voices.Item($i).GetDescription() -eq 'VW Paul') { $target = $voices.Item($i); break }
}
if (-not $target) {
    Write-Error "VW Paul not found in SAPI voice list."
    exit 11
}
$voice.Voice = $target
Write-Host "Voice: $($voice.Voice.GetDescription()) | rate=$($voice.Rate) vol=$($voice.Volume) | shard=$ShardIndex/$ShardCount"

$lines = Get-Content $PromptsFile
$done = 0; $skipped = 0; $failed = 0

foreach ($line in $lines) {
    if (-not $line.Trim()) { continue }
    $parts = $line -split "`t", 2
    if ($parts.Count -ne 2) { continue }
    $id = $parts[0]; $text = $parts[1]

    if ([int]$id % $ShardCount -ne $ShardIndex) { continue }

    $outPath = Join-Path $OutDir "$id.wav"
    if (Test-Path $outPath) { $skipped++; continue }

    $fs = $null
    try {
        $fs = New-Object -ComObject SAPI.SpFileStream
        $fs.Open($outPath, 3, $false)   # SSFMCreateForWrite
        $voice.AudioOutputStream = $fs
        [void]$voice.Speak($text, 0)
        $fs.Close()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($fs)
        $fs = $null
        $done++
        if ($done % 200 -eq 0) {
            Write-Host "  [$ShardIndex] $done spoken (skip=$skipped fail=$failed)"
        }
    } catch {
        $msg = "$id`t$($_.Exception.Message)"
        Add-Content -Path $ErrorLog -Value $msg
        $failed++
        if ($fs) {
            try { $fs.Close() } catch {}
            try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($fs) } catch {}
        }
        Remove-Item $outPath -Force -ErrorAction SilentlyContinue
    } finally {
        $voice.AudioOutputStream = $null
    }
}

Write-Host "Shard $ShardIndex done: spoken=$done skipped=$skipped failed=$failed"
