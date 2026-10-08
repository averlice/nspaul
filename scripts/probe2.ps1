# 32-bit probe #2: proper engine load + COM activation by CLSID
$ErrorActionPreference = 'Continue'

Add-Type -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern IntPtr LoadLibraryEx(string lpFileName, IntPtr hFile, uint dwFlags);
[DllImport("kernel32.dll")]
public static extern bool FreeLibrary(IntPtr hModule);
'@ -Name Native -Namespace Probe2 | Out-Null

$dll = 'C:\Program Files (x86)\VW\VT\Paul\M16-SAPI5\lib\vtengsapi50.dll'

foreach ($flag in 0, 8) {
    $h = [Probe2.Native]::LoadLibraryEx($dll, [IntPtr]::Zero, [uint32]$flag)
    $err = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    "flags=$flag handle=$h err=$err"
    if ($h -ne [IntPtr]::Zero) { [void][Probe2.Native]::FreeLibrary($h) }
}

# COM activation by CLSID from the 32-bit registry view
$clsid = '{9892E74A-B96D-4747-9D2A-87646C3D9E4C}'
try {
    $t = [Type]::GetTypeFromCLSID($clsid, $true)
    "Type.GetTypeFromCLSID: $t"
    $obj = [Activator]::CreateInstance($t)
    "COM CreateInstance: OK type=$($obj.GetType().FullName)"
} catch {
    "COM CreateInstance: FAIL - $($_.Exception.Message) [HResult=$($_.Exception.HResult)]"
}

# Try System.Speech SelectVoice once more after warm COM
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $s.SelectVoice('VW Paul')
    "SelectVoice OK -> $($s.Voice.Name)"
} catch {
    "SelectVoice FAIL: $($_.Exception.Message)"
}
$s.Dispose()
