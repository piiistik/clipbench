param(
    [Parameter(
        Mandatory = $true,
        Position = 0,
        ValueFromRemainingArguments = $true
    )]
    [int[]]$Numbers
)

$totalMs = 0

for ($i = 0; $i -lt $Numbers.Length; $i++) {
    $index = $i + 1
    $value = $Numbers[$i]

    # integer-safe power calculation
    $power = 1
    for ($j = 0; $j -lt $index; $j++) {
        $power *= $value
    }

    $totalMs += $power
}

Write-Host "Computed sleep time: $totalMs ms"

if ($totalMs -gt 0) {
    Start-Sleep -Milliseconds $totalMs
}

Write-Host "Done."