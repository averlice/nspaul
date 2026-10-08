# 32-bit probe #3: raw SAPI COM path - set token by path, speak to WAV stream
$ErrorActionPreference = 'Stop'
$out = 'C:\paul\test.wav'
if (Test-Path $out) { Remove-Item $out -Force }

$t = New-Object -ComObject SAPI.SpObjectToken
try {
    $t.SetId('HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\VW Paul', $false)
    "token desc: $($t.GetDescription())"
} catch {
    "token SetId FAIL: $($_.Exception.Message) [HResult=$($_.Exception.HResult)]"
    exit 1
}

$v = New-Object -ComObject SAPI.SpVoice
$v.Voice = $t
"assigned voice: $($v.Voice.GetDescription())"
"rate=$($v.Rate) volume=$($v.Volume)"

$fs = New-Object -ComObject SAPI.SpFileStream
$fs.Open($out, 3, $false)   # SSFMCreateForWrite
$v.AudioStream = $fs
$len = $v.Speak('The quick brown fox jumps over the lazy dog.', 0)
$fs.Close()
$fs = $null
"spoken length (100ns units): $len"
"file exists: $(Test-Path $out) size=$((Get-Item $out).Length)"
