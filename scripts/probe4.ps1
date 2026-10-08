# 32-bit probe #4: dump the COM dispatch surface of SAPI objects
$ErrorActionPreference = 'Continue'

"=== SAPI.SpVoice ==="
$v = New-Object -ComObject SAPI.SpVoice
$v | Get-Member -MemberType Method, Property, Event | Select-Object -ExpandProperty Name -Unique | Sort-Object

"`n=== SAPI.SpObjectTokenCategory ==="
$cat = New-Object -ComObject SAPI.SpObjectTokenCategory
$cat | Get-Member -MemberType Method, Property | Select-Object -ExpandProperty Name -Unique | Sort-Object

"`n=== SAPI.SpObjectToken ==="
$t = New-Object -ComObject SAPI.SpObjectToken
$t | Get-Member -MemberType Method, Property | Select-Object -ExpandProperty Name -Unique | Sort-Object

"`n=== SpVoice.Voices raw ==="
try {
    $col = $v.Voices
    "null? $($null -eq $col)  type: $(if ($col) { $col.GetType().FullName } else { 'NULL' })"
    if ($col) {
        "count: $($col.Count)"
        for ($i = 0; $i -lt [Math]::Min(5, $col.Count); $i++) { "  [$i] $($col.Item($i).GetDescription())" }
    }
} catch {
    "Voices FAIL: $($_.Exception.Message)"
}
