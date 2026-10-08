param(
    [string]$Text = "The quick brown fox jumps over the lazy dog.",
    [string]$Out = "C:\paul\test.wav"
)

Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $s.SelectVoice("VW Paul")
    if ($s.Voice.Name -ne "VW Paul") {
        Write-Error ("Wrong voice selected: " + $s.Voice.Name)
        exit 2
    }
    Write-Host ("Voice: " + $s.Voice.Name + " | Rate: " + $s.Rate + " | Volume: " + $s.Volume)
    $s.SetOutputToWaveFile($Out)
    $s.Speak($Text)
    Write-Host ("Wrote " + $Out)
    exit 0
}
finally {
    $s.Dispose()
}
