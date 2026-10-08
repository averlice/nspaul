# 32-bit probe #5: correct API - GetVoices() -> find VW Paul -> speak to WAV
$ErrorActionPreference = 'Stop'
$out = 'C:\paul\test.wav'
if (Test-Path $out) { Remove-Item $out -Force }

$v = New-Object -ComObject SAPI.SpVoice
$voices = $v.GetVoices()
"voice count: $($voices.Count)"
for ($i = 0; $i -lt $voices.Count; $i++) {
    $t = $voices.Item($i)
    $d = $t.GetDescription()
    if ($d -like '*Paul*' -or $d -like '*VW*') { "  [$i] $d" }
}

$target = $null
for ($i = 0; $i -lt $voices.Count; $i++) {
    if ($voices.Item($i).GetDescription() -eq 'VW Paul') { $target = $voices.Item($i); break }
}
if (-not $target) { throw 'VW Paul not found in GetVoices()' }

$v.Voice = $target
"assigned: $($v.Voice.GetDescription())  rate=$($v.Rate) vol=$($v.Volume)"

$fs = New-Object -ComObject SAPI.SpFileStream
$fs.Open($out, 3, $false)  # SSFMCreateForWrite
$v.AudioOutputStream = $fs
[void]$v.Speak('The quick brown fox jumps over the lazy dog.', 0)
$fs.Close()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($fs) | Out-Null

"exists: $(Test-Path $out)  size: $((Get-Item $out).Length) bytes"
