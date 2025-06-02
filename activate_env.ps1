$envPath = poetry env info --path
if ($envPath) {
    & "$envPath\Scripts\activate.ps1"
    Write-Host "Environment activated. Use 'deactivate' to exit."
} else {
    Write-Host "No Poetry environment found. Run 'poetry install' to create one."
}