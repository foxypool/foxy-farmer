$chiaBinDirectory = "$env:userprofile\AppData\Local\Programs\Chia\resources\app.asar.unpacked\daemon"
$chiaBinPath = "$chiaBinDirectory\chia.exe"
if (!(Test-Path -Path $chiaBinPath -PathType Leaf)) {
    Write-Output "Did not find chia, is chia installed?"
    Read-Host -Prompt "Press any key to exit"
    exit
}

$foxyHarvesterChiaRootPath = "$env:userprofile\.foxy-harvester\mainnet"
$env:CHIA_ROOT = $foxyHarvesterChiaRootPath
if (!(Test-Path -Path $foxyHarvesterChiaRootPath)) {
    $foxyFarmerCaPath = "foxy-farmer-ca"
    if (!(Test-Path -Path $foxyFarmerCaPath)) {
        Write-Output "Did not find foxy-farmer-ca directory"
        Read-Host -Prompt "Press any key to exit"
        exit
    }
    $foxyFarmerPeerHost = Read-Host -Prompt 'Input the IP of foxy-farmer'
    Write-Output "Bootstrapping new harvester .."
    Start-Process -NoNewWindow -Wait -FilePath "$chiaBinPath" -ArgumentList "init --create-certs $foxyFarmerCaPath"
    $chiaConfigPath = "$env:userprofile\.chia\mainnet\config\config.yaml"
    $foxyHarvesterChiaConfigPath = "$foxyHarvesterChiaRootPath\config\config.yaml"
    if (Test-Path -Path $chiaConfigPath -PathType Leaf) {
        Copy-Item -Path $chiaConfigPath -Destination $foxyHarvesterChiaConfigPath -Force
    }
    Start-Process -NoNewWindow -Wait -FilePath "$chiaBinPath" -ArgumentList "configure --set-harvester-port 18448 --set-farmer-peer $foxyFarmerPeerHost`:18447 --set-log-level INFO"
    ((Get-Content -path $foxyHarvesterChiaConfigPath -Raw) -replace 'rpc_port: 8560','rpc_port: 18560') | Set-Content -Path $foxyHarvesterChiaConfigPath
    ((Get-Content -path $foxyHarvesterChiaConfigPath -Raw) -replace 'log_stdout: false','log_stdout: true') | Set-Content -Path $foxyHarvesterChiaConfigPath
}

try {
    $daemonProcess = Start-Process -NoNewWindow -PassThru -FilePath "$chiaBinPath" -ArgumentList " run_daemon"
    Start-Sleep -Seconds 2
    Start-Process -NoNewWindow -FilePath "$chiaBinPath" -ArgumentList "start harvester"
    $daemonProcess.WaitForExit()
} finally {
    $harvesterPidFile = "$foxyHarvesterChiaRootPath\run\chia_harvester.pid"
    if (Test-Path -Path $harvesterPidFile -PathType Leaf) {
        $harvesterPid = Get-Content -path $harvesterPidFile -Raw
        Stop-Process -Id $harvesterPid
    }
}
