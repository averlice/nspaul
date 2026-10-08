# Runs in 32-bit PowerShell. Probes why VW Paul fails SelectVoice.
$ErrorActionPreference = 'Continue'

# 1. Can we load the engine DLL in this (32-bit) process?
Add-Type -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern IntPtr LoadLibraryEx(string lpFileName, IntPtr hFile, uint dwFlags);
[DllImport("kernel32.dll")]
public static extern bool FreeLibrary(IntPtr hModule);
'@ -Name Native -Namespace Probe | Out-Null

$dll = 'C:\Program Files (x86)\VW\VT\Paul\M16-SAPI5\lib\vtengsapi50.dll'
$h = [Probe.Native]::LoadLibraryEx($dll, [IntPtr]::Zero, 0)
"LoadLibrary handle: $h"
"LoadLibrary error : $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
if ($h -ne [IntPtr]::Zero) { [void][Probe.Native]::FreeLibrary($h) }

# 2. Can SAPI COM activate the engine CLSID?
try {
    $eng = New-Object -ComObject vtengSAPI50.Class
    "COM activation: OK ($eng)"
} catch {
    "COM activation: FAIL - $($_.Exception.Message) [$($_.Exception.HResult)]"
}

# 3. Enumerate SAPI tokens directly from the 32-bit registry and try each API path
$tokensRoot = 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Speech\Voices\Tokens'
Get-ChildItem $tokensRoot | ForEach-Object {
    $n = (Get-ItemProperty $_.PSPath).'(default)'
    if ($n -eq 'VW Paul') { "Found token key: $($_.PSChildName) -> $n" }
}

# 4. SpVoice enumeration via reflection-style call
$v = New-Object -ComObject SAPI.SpVoice
try {
    $col = $v.get_Voices()
    "SpVoice.get_Voices() type: $($col.GetType().FullName)"
} catch {
    "SpVoice.get_Voices() FAIL: $($_.Exception.Message)"
}

# 5. System.Speech: exact SelectVoice diagnostics
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$vp = ($s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -eq 'VW Paul' })
"VW Paul installed: $([bool]$vp), enabled: $($vp.Enabled)"
try {
    $s.SelectVoice('VW Paul')
    "SelectVoice OK -> $($s.Voice.Name)"
} catch {
    "SelectVoice FAIL: $($_.Exception.Message)"
}
$s.Dispose()
