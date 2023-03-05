$foxyFarmerChiaRootPath = "$env:userprofile\.foxy-farmer\mainnet"
if (!(Test-Path -Path $foxyFarmerChiaRootPath)) {
    Write-Output "Did not find .foxy-farmer directory, do you have foxy-farmer installed?"
    Read-Host -Prompt "Press any key to exit"
    exit
}
$foxyHarvesterPath = "foxy-harvester"
if (Test-Path -Path $foxyHarvesterPath) {
    Write-Output "foxy-harvester directory already exists, you can copy it to your harvesters and run the run_harvester.ps1 script there"
    Read-Host -Prompt "Press any key to exit"
    exit
}
New-Item $foxyHarvesterPath -ItemType Directory
$foxyFarmerCaPath = "$foxyHarvesterPath\foxy-farmer-ca"
Copy-Item -Path "$foxyFarmerChiaRootPath\config\ssl\ca" -Destination $foxyFarmerCaPath -Recurse
Copy-Item -Path "run_harvester.ps1" -Destination $foxyHarvesterPath
