Param(
  [string]$BaseUrl = "http://localhost:8000",
  [int]$TimeoutSec = 30
)

function Wait-Health {
  Param([string]$Url, [int]$Tries = 60)
  for ($i = 0; $i -lt $Tries; $i++) {
    try {
      $resp = Invoke-RestMethod -Method Get "$Url/health" -TimeoutSec 5
      if ($resp.status -eq 'ok') { return $true }
    } catch { Start-Sleep -Seconds 1 }
  }
  return $false
}

function Start-Order {
  Param([string]$OrderId, [string]$PaymentId)
  $url = "$BaseUrl/orders/$OrderId/start?payment_id=$PaymentId"
  return Invoke-RestMethod -Method Post $url -TimeoutSec 10
}

function Update-Address {
  Param([string]$OrderId, [hashtable]$Address)
  $url = "$BaseUrl/orders/$OrderId/signals/update_address"
  $body = ($Address | ConvertTo-Json -Depth 5)
  return Invoke-RestMethod -Method Post $url -ContentType 'application/json' -Body $body -TimeoutSec 10
}

function Cancel-Order {
  Param([string]$OrderId)
  $url = "$BaseUrl/orders/$OrderId/signals/cancel"
  return Invoke-RestMethod -Method Post $url -TimeoutSec 10
}

function Get-Status {
  Param([string]$OrderId)
  $url = "$BaseUrl/orders/$OrderId/status"
  return Invoke-RestMethod -Method Get $url -TimeoutSec 10
}

if (-not (Wait-Health -Url $BaseUrl)) {
  Write-Error "API health check failed at $BaseUrl"
  exit 1
}

# Test 1: Happy path
$order1 = [guid]::NewGuid().Guid
$payment1 = [guid]::NewGuid().Guid
Write-Host "Starting happy-path workflow: order=$order1 payment=$payment1"
$start1 = Start-Order -OrderId $order1 -PaymentId $payment1
Update-Address -OrderId $order1 -Address @{ street = '123 Main'; city = 'SF' }

$deadline = (Get-Date).AddSeconds($TimeoutSec)
do {
  Start-Sleep -Milliseconds 800
  try { $st = Get-Status -OrderId $order1 } catch { continue }
  $state = $st.status.state
  Write-Host "status=$state"
  if ($state -eq 'completed') { break }
  if ($state -eq 'cancelled') { Write-Error "Unexpected cancelled in happy path"; exit 1 }
} while ((Get-Date) -lt $deadline)

if ($st.status.state -ne 'completed') {
  Write-Error "Happy path did not complete in $TimeoutSec seconds"
  exit 1
}
Write-Host "Happy path completed"

# Test 2: Cancel path
$order2 = [guid]::NewGuid().Guid
$payment2 = [guid]::NewGuid().Guid
Write-Host "Starting cancel workflow: order=$order2 payment=$payment2"
$start2 = Start-Order -OrderId $order2 -PaymentId $payment2
Cancel-Order -OrderId $order2 | Out-Null

$deadline2 = (Get-Date).AddSeconds([Math]::Min($TimeoutSec, 15))
do {
  Start-Sleep -Milliseconds 500
  try { $st2 = Get-Status -OrderId $order2 } catch { continue }
  $state2 = $st2.status.state
  Write-Host "status2=$state2"
  if ($state2 -eq 'cancelled') { break }
} while ((Get-Date) -lt $deadline2)

if ($st2.status.state -ne 'cancelled') {
  Write-Error "Cancel path did not reach cancelled state"
  exit 1
}
Write-Host "Cancel path completed"

Write-Host "All e2e tests passed"
exit 0


