<#
.SYNOPSIS
  Sleep a mostly-random small number of milliseconds, but spike near configurable centers.

.DESCRIPTION
  Usage: pwsh .\noisy_peak_sleep.ps1 42 37

  The script computes a baseline random sleep in [0, NormalMaxMs).
  For each configured center (cx,cy) it computes a Gaussian-like contribution:
      contribution = exp( - (dist^2) / (2 * sigma^2) )
  and uses the largest contribution to scale the sleep from baseline up toward SpikeSleepMs.
  The spike is steep/ local when Sigma is small; set SpikeRadius to roughly the radius
  (in same units as inputs) you want the spike to affect and adjust Sharpness for steepness.

#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [int]$X,

    [Parameter(Mandatory=$true, Position=1)]
    [int]$Y
)

####### CONFIGURABLE VARIABLES (tweak these) #######
# Centers where spikes occur. List of 2-element arrays: @([int,int], [int,int], ...)
# Default: (100,100), (200,200), ... (900,900)
$Centers = @(
    @(100,100), @(200,200), @(300,300), @(400,400), @(500,500),
    @(600,600), @(700,700), @(800,800), @(900,900)
)

# Maximum "normal" sleep (exclusive): baseline random ms will be in [0, NormalMaxMs)
$NormalMaxMs = 20

# Sleep at spike peak (ms)
$SpikeSleepMs = 500

# Spike radius (rough scale in same units as inputs). The spike influence is noticeable roughly within this radius.
$SpikeRadius = 15

# Sharpness exponent applied to Gaussian contribution to make the climb steeper.
# Larger values -> narrower/steeper peak. Try 1..6. Default 3 gives quite local steep peaks.
$Sharpness = 3

# Extra random jitter added/subtracted after interpolation (signed). Set 0 to disable.
$JitterMs = 0

# Random seed: $null for system default randomness, or set an int for reproducible behavior.
$Seed = $null
#####################################################

# Optional reproducible randomness
if ($null -ne $Seed) { Set-Random -Seed $Seed }

# Helper: Euclidean distance
function Get-Distance {
    param([double]$x1, [double]$y1, [double]$x2, [double]$y2)
    return [math]::Sqrt((($x1 - $x2) * ($x1 - $x2)) + (($y1 - $y2) * ($y1 - $y2)))
}

# Convert SpikeRadius to sigma for Gaussian: sigma controls width.
# We use sigma = SpikeRadius / 2 so that at dist = SpikeRadius the gaussian is small.
# You can adjust mapping here if you want a different falloff.
$sigma = [double]$SpikeRadius / 2.0
if ($sigma -le 0) { $sigma = 1.0 }

# Baseline random ms (integer)
$baselineMs = Get-Random -Maximum $NormalMaxMs

# Evaluate contribution from each center and take the maximum (local maxima behavior)
$maxContribution = 0.0
foreach ($c in $Centers) {
    $cx = [double]$c[0]
    $cy = [double]$c[1]
    $d = Get-Distance -x1 $X -y1 $Y -x2 $cx -y2 $cy

    # Gaussian-like contribution, 0..1
    $contrib = [math]::Exp( - ( $d * $d ) / ( 2.0 * $sigma * $sigma ) )

    # apply sharpness power to make peaks steeper (keeps value in 0..1)
    if ($Sharpness -ne 1) {
        $contrib = [math]::Pow($contrib, [double]$Sharpness)
    }

    if ($contrib -gt $maxContribution) { $maxContribution = $contrib }
}

# Interpolate between baseline and spike peak using the strongest local contribution
# sleepMs = baseline + (SpikeSleepMs - baseline) * maxContribution
$sleepMsFloat = $baselineMs + ( ($SpikeSleepMs - $baselineMs) * $maxContribution )

# Add optional jitter
if ($JitterMs -ne 0) {
    # jitter in range [-JitterMs, +JitterMs]
    $j = (Get-Random -Minimum (-$JitterMs) -Maximum ($JitterMs + 1))
    $sleepMsFloat += $j
}

# Clamp to [0, SpikeSleepMs]
if ($sleepMsFloat -lt 0) { $sleepMsFloat = 0 }
if ($sleepMsFloat -gt $SpikeSleepMs) { $sleepMsFloat = $SpikeSleepMs }

# Final integer milliseconds
$sleepMs = [int][math]::Round($sleepMsFloat)

# Output diagnostics (can be removed or replaced by -Verbose switch)
Write-Host "Input: ($X, $Y)"
Write-Host "Baseline random ms: $baselineMs"
Write-Host "Max spike contribution: $([math]::Round($maxContribution, 4))"
Write-Host "Sleeping for $sleepMs ms"
Start-Sleep -Milliseconds $sleepMs
Write-Host "Done."