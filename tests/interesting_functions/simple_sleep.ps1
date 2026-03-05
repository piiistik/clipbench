param(
    [Parameter(Position = 0, Mandatory = $true)]
    [int]$a,

    [Parameter(Position = 1, Mandatory = $true)]
    [int]$b
)

Start-Sleep -Milliseconds (($a + $b) / 1e12)
