<#
 One-shot Docker + Kubernetes + monitoring verification (Windows PowerShell 5.1 or 7).

 Run from anywhere:   powershell -ExecutionPolicy Bypass -File scripts\deploy_and_verify.ps1
 Options:             -SkipK8s   -SkipMonitoring   -NoPause

 What it does
   1. Docker : build image, run container, hit /health, /predict, /predict/batch, invalid input (422)
   2. K8s    : apply deployment/, wait for rollout, port-forward the Service, hit the same endpoints
   3. Monitor: start API + Prometheus + Grafana (docker compose), send traffic, check Prometheus target is UP
 Text proof is saved to screenshots\evidence\*.txt  (you still take the PNG screenshots listed in
 screenshots\README.md - the script pauses at the right moments).
 Prerequisites: Docker Desktop running; for step 2 a Kubernetes context (Docker Desktop Kubernetes or Minikube).
#>
param([switch]$SkipK8s, [switch]$SkipMonitoring, [switch]$NoPause)

$ErrorActionPreference = "Continue"      # native commands write progress to stderr; we check exit codes ourselves
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Out = Join-Path $Root "screenshots\evidence"
New-Item -ItemType Directory -Force $Out | Out-Null
$Results = New-Object System.Collections.ArrayList

function Step($m)   { Write-Host ""; Write-Host "=== $m ===" -ForegroundColor Cyan }
function Save($n,$t){ $t | Out-File -Encoding utf8 (Join-Path $Out $n) }
function Pass($m)   { Write-Host "[PASS] $m" -ForegroundColor Green; [void]$Results.Add("PASS  $m") }
function Fail($m)   { Write-Host "[FAIL] $m" -ForegroundColor Red;   [void]$Results.Add("FAIL  $m") }
function Pause-ForShot($msg) {
    if (-not $NoPause) { Read-Host "`n>> $msg  (press Enter to continue)" | Out-Null }
}
function Run-Capture($file, [scriptblock]$cmd) {
    # run a native command, merge stderr into stdout as plain strings, show it and save it
    $o = & $cmd 2>&1 | ForEach-Object { "$_" }
    $o | Out-File -Encoding utf8 $file
    $o | ForEach-Object { Write-Host $_ }
}
function Wait-Health($url, $tries) {
    for ($i = 0; $i -lt $tries; $i++) {
        try { $r = Invoke-RestMethod -Uri "$url/health" -TimeoutSec 3; if ($r.status -eq "healthy") { return $true } } catch { }
        Start-Sleep -Seconds 2
    }
    return $false
}
function Test-Api($base, $tag) {
    $log = New-Object System.Collections.ArrayList
    try {
        $h = Invoke-RestMethod -Uri "$base/health"
        [void]$log.Add("GET /health -> " + ($h | ConvertTo-Json -Compress))
        $single = Get-Content (Join-Path $Root "samples\patient.json") -Raw
        $p = Invoke-RestMethod -Method Post -Uri "$base/predict" -ContentType "application/json" -Body $single
        [void]$log.Add("POST /predict (UCI row 1, true label 0) -> " + ($p | ConvertTo-Json -Compress))
        $batchBody = '{"records":' + (Get-Content (Join-Path $Root "samples\patients_batch.json") -Raw) + '}'
        $b = Invoke-RestMethod -Method Post -Uri "$base/predict/batch" -ContentType "application/json" -Body $batchBody
        [void]$log.Add("POST /predict/batch (UCI rows 1 and 2) -> " + ($b | ConvertTo-Json -Compress -Depth 5))
        $badBody = $single -replace '"thal"\s*:\s*6', '"thal":2'
        $code = 0
        try { Invoke-RestMethod -Method Post -Uri "$base/predict" -ContentType "application/json" -Body $badBody | Out-Null }
        catch { $code = [int]$_.Exception.Response.StatusCode }
        [void]$log.Add("POST /predict with invalid thal=2 -> HTTP $code (expected 422)")
        $log | ForEach-Object { Write-Host $_ }
        Save "$tag`_api_calls.txt" $log
        if ($p.label -and $b.count -eq 2 -and $code -eq 422) { Pass "$tag API: /health, /predict, /predict/batch, validation (422)"; return $true }
        Fail "$tag API responses unexpected (see screenshots\evidence\$tag`_api_calls.txt)"; return $false
    } catch {
        Fail "$tag API call error: $($_.Exception.Message)"; return $false
    }
}

# ---------------------------------------------------------------- 0. prerequisites
Step "0. Prerequisites"
docker info *> $null
if ($LASTEXITCODE -ne 0) { Fail "Docker daemon not reachable - start Docker Desktop and re-run"; $Results; exit 1 }
Pass "Docker daemon reachable"
if (-not (Test-Path (Join-Path $Root "model_artifacts\model.joblib"))) {
    Fail "model_artifacts\model.joblib missing - run: python src\train.py"; $Results; exit 1
}

# ---------------------------------------------------------------- 1. Docker
Step "1. Docker build"
Run-Capture (Join-Path $Out "05_docker_build.txt") { docker build --progress=plain -t heart-api:latest . }
if ($LASTEXITCODE -ne 0) { Fail "docker build failed (log: screenshots\evidence\05_docker_build.txt)"; $Results; exit 1 }
Pass "docker build heart-api:latest"
Run-Capture (Join-Path $Out "05_docker_images.txt") { docker images heart-api:latest }

# the pickled model must be loaded by the same scikit-learn version that trained it
$trainedWith = (Get-Content (Join-Path $Root "model_artifacts\metadata.json") -Raw | ConvertFrom-Json).sklearn_version
$servedWith  = (docker run --rm --entrypoint python heart-api:latest -c "import sklearn; print(sklearn.__version__)").Trim()
if ($trainedWith -and $trainedWith -ne $servedWith) {
    Write-Host "WARNING: model trained with scikit-learn $trainedWith but image has $servedWith." -ForegroundColor Yellow
    Write-Host "         Fix: pin scikit-learn==$trainedWith in requirements-serve.txt (or retrain: python src\train.py) and rebuild." -ForegroundColor Yellow
    [void]$Results.Add("WARN  sklearn version mismatch train=$trainedWith image=$servedWith")
} else { Pass "scikit-learn version matches (train=$trainedWith image=$servedWith)" }

Step "1b. Docker run + test"
docker rm -f heart_local 2>$null | Out-Null
docker run -d --name heart_local -p 8000:8000 heart-api:latest | Out-Null
if (Wait-Health "http://localhost:8000" 30) {
    Pass "container healthy on :8000"
    $who = (docker exec heart_local whoami).Trim()
    if ($who -ne "root") { Pass "container runs as non-root user ($who)" } else { Fail "container runs as root" }
    Test-Api "http://localhost:8000" "06_docker" | Out-Null
    Run-Capture (Join-Path $Out "06_docker_ps.txt") { docker ps --filter name=heart_local --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}" }
    Run-Capture (Join-Path $Out "06_docker_logs.txt") { docker logs --tail 8 heart_local }
    Pause-ForShot "Take screenshots 05_docker_build / 06_docker_run_curl now; also open http://localhost:8000/docs for 07_swagger_docs"
} else {
    Fail "container did not become healthy"
    Run-Capture (Join-Path $Out "06_docker_logs.txt") { docker logs heart_local }
}
docker rm -f heart_local 2>$null | Out-Null

# ---------------------------------------------------------------- 2. Kubernetes
if (-not $SkipK8s) {
    Step "2. Kubernetes"
    $ctx = (kubectl config current-context 2>$null)
    if (-not $ctx) {
        Fail "no kubectl context - enable Kubernetes in Docker Desktop (Settings > Kubernetes) or run: minikube start"
    } else {
        Write-Host "kubectl context: $ctx"
        Save "08_k8s_context.txt" $ctx
        if ($ctx -like "*minikube*") { Write-Host "Loading image into Minikube..."; minikube image load heart-api:latest }
        elseif ($ctx -like "kind-*") { Write-Host "Loading image into kind...";     kind load docker-image heart-api:latest }
        Run-Capture (Join-Path $Out "08_k8s_apply.txt") { kubectl apply -f deployment/ }
        Run-Capture (Join-Path $Out "08_k8s_rollout.txt") { kubectl rollout status deployment/heart-api --timeout=180s }
        if ($LASTEXITCODE -eq 0) {
            Pass "deployment rolled out (2 replicas ready)"
            Run-Capture (Join-Path $Out "08_k8s_pods.txt") { kubectl get pods,svc,hpa -o wide }
            $pf = Start-Process kubectl -ArgumentList "port-forward","svc/heart-api-service","8080:80" -PassThru -WindowStyle Hidden
            Start-Sleep -Seconds 6
            if (Wait-Health "http://localhost:8080" 15) { Test-Api "http://localhost:8080" "09_k8s" | Out-Null }
            else { Fail "Service not reachable through port-forward" }
            Run-Capture (Join-Path $Out "09_k8s_logs.txt") { kubectl logs deployment/heart-api --tail=6 }
            Pause-ForShot "Take screenshots 08_k8s_pods (kubectl get pods,svc) and 09_k8s_service_url (curl via http://localhost:8080) now"
            if ($pf -and -not $pf.HasExited) { Stop-Process -Id $pf.Id -Force }
        } else {
            Fail "rollout failed - usually ImagePullBackOff (image not visible to the cluster)"
            Run-Capture (Join-Path $Out "08_k8s_describe.txt") { kubectl describe pods -l app=heart-api }
            Write-Host "Hint: Docker Desktop kind-mode needs 'Use containerd for pulling and storing images' enabled; Minikube needs 'minikube image load heart-api:latest'." -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------- 3. Monitoring
if (-not $SkipMonitoring) {
    Step "3. Prometheus + Grafana (docker compose)"
    Run-Capture (Join-Path $Out "10_compose_up.txt") { docker compose -f monitoring/docker-compose.monitoring.yml up -d --build }
    if ($LASTEXITCODE -eq 0 -and (Wait-Health "http://localhost:8000" 30)) {
        $row1 = Get-Content (Join-Path $Root "samples\patient.json") -Raw
        $row2 = '{"age":67,"sex":1,"cp":4,"trestbps":160,"chol":286,"fbs":0,"restecg":2,"thalach":108,"exang":1,"oldpeak":1.5,"slope":2,"ca":3,"thal":3}'
        1..20 | ForEach-Object {
            $body = $row1
            if ($_ % 2 -eq 0) { $body = $row2 }
            Invoke-RestMethod -Method Post -Uri "http://localhost:8000/predict" -ContentType "application/json" -Body $body | Out-Null
        }
        Write-Host "Sent 20 predictions; waiting for Prometheus to scrape..."
        Start-Sleep -Seconds 20
        try {
            $t = Invoke-RestMethod "http://localhost:9090/api/v1/targets"
            $health = ($t.data.activeTargets | Where-Object { $_.labels.job -eq "heart-api" }).health
            Save "11_prometheus_targets.txt" ($t | ConvertTo-Json -Depth 6)
            if ($health -eq "up") { Pass "Prometheus target heart-api is UP" } else { Fail "Prometheus target heart-api health = $health" }
            $q = Invoke-RestMethod "http://localhost:9090/api/v1/query?query=heart_predictions_total"
            Save "11_prometheus_query.txt" ($q | ConvertTo-Json -Depth 6)
            Write-Host ("heart_predictions_total series: " + $q.data.result.Count)
        } catch { Fail "Prometheus query failed: $($_.Exception.Message)" }
        try { $g = Invoke-RestMethod "http://localhost:3000/api/health"; Pass "Grafana reachable (db: $($g.database))" } catch { Fail "Grafana not reachable on :3000" }
        Pause-ForShot "Take screenshots 10_grafana (http://localhost:3000, admin/admin > Dashboards) and 11_prometheus_targets (http://localhost:9090/targets)"
    } else { Fail "compose stack did not start (see screenshots\evidence\10_compose_up.txt)" }
    Write-Host "Stop the stack later with: docker compose -f monitoring/docker-compose.monitoring.yml down"
}

# ---------------------------------------------------------------- summary
Step "Summary"
$Results | ForEach-Object { Write-Host $_ }
Save "00_summary.txt" $Results
Write-Host "`nEvidence files: $Out"
