param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

Set-Location "C:\Ranabir - C Drive\GitHub\Barrier Led Engagement\barrier_agent"

Write-Host "Checking git status..."
git status

Write-Host "Adding changes..."
git add .

Write-Host "Committing changes..."
git commit -m $Message

if ($LASTEXITCODE -ne 0) {
    Write-Host "Commit did not complete. There may be nothing to commit, or there may be an error."
    exit $LASTEXITCODE
}

Write-Host "Pushing to GitHub..."
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "Push successful. Streamlit should auto-redeploy shortly."
} else {
    Write-Host "Push failed. Check the error above."
}