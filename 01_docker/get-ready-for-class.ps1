$ErrorActionPreference = "Stop"

$requiredImages = @(
  "postgres",
  "maven:3.9.9-eclipse-temurin-17",
  "eclipse-temurin:17-jre",
  "node:20-alpine",
  "python:3.12-slim"
)

$requiredModel = "ai/llama3.2"

function Write-Log {
  param([string]$Message)
  Write-Host ""
  Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message)
}

function Require-Command {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

function Choose-Platform {
  Write-Host ""
  Write-Host "Select your Docker target platform:"
  Write-Host "  1) linux/arm64 (Apple Silicon / ARM on Windows host tooling)"
  Write-Host "  2) linux/amd64 (Intel / x86_64) [recommended]"
  Write-Host "  3) Keep Docker default"
  $choice = Read-Host "Choice [1/2/3]"

  switch ($choice) {
    ""  { $env:DOCKER_DEFAULT_PLATFORM = "linux/amd64" }
    "1" { $env:DOCKER_DEFAULT_PLATFORM = "linux/arm64" }
    "2" { $env:DOCKER_DEFAULT_PLATFORM = "linux/amd64" }
    "3" { Remove-Item Env:DOCKER_DEFAULT_PLATFORM -ErrorAction SilentlyContinue }
    default { throw "Unknown choice: $choice" }
  }

  if ($env:DOCKER_DEFAULT_PLATFORM) {
    Write-Log "Using DOCKER_DEFAULT_PLATFORM=$($env:DOCKER_DEFAULT_PLATFORM)"
  }
  else {
    Write-Log "Using Docker default platform"
  }
}

Write-Log "Checking Docker CLI"
Require-Command "docker"

Write-Log "Checking Docker daemon"
docker info | Out-Null

Write-Log "Checking Docker Compose"
docker compose version | Out-Null

Write-Log "Checking Docker Model Runner"
docker model version | Out-Null

Choose-Platform

foreach ($image in $requiredImages) {
  Write-Log "Pulling image $image"
  docker pull $image
}

Write-Log "Pulling model $requiredModel"
docker model pull $requiredModel

@"

 __   __  _______  __   __    _______  ______    _______
|  | |  ||       ||  | |  |  |   _   ||    _ |  |       |
|  |_|  ||   _   ||  | |  |  |  |_|  ||   | ||  |    ___|
|       ||  | |  ||  |_|  |  |       ||   |_||_ |   |___
|_     _||  |_|  ||       |  |       ||    __  ||    ___|
  |   |  |       ||       |  |   _   ||   |  | ||   |___
  |___|  |_______||_______|  |__| |__||___|  |_||_______|

                   YOU ARE ALL SET!

"@ | Write-Host
