#Requires -Version 5.1
<#
.SYNOPSIS
    GeekCode Installation Script for Windows

.DESCRIPTION
    This script installs GeekCode on Windows systems.

.PARAMETER Version
    Specific version to install (default: latest)

.PARAMETER FromSource
    Path to source directory for development installation

.EXAMPLE
    .\install.ps1

.EXAMPLE
    .\install.ps1 -Version 0.1.0

.EXAMPLE
    .\install.ps1 -FromSource C:\path\to\geekcode
#>

param(
    [string]$Version = "latest",
    [string]$FromSource = "",
    [switch]$Help
)

# Configuration
$ErrorActionPreference = "Stop"
$GeekCodeConfigDir = Join-Path $env:USERPROFILE ".geekcode"
$PythonMinVersion = [version]"3.8"

# Colors
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
    exit 1
}

function Show-Banner {
    Write-Host ""
    Write-ColorOutput "  ╔═══════════════════════════════════════╗" "Blue"
    Write-ColorOutput "  ║                                       ║" "Blue"
    Write-ColorOutput "  ║   ██████╗ ███████╗███████╗██╗  ██╗   ║" "Blue"
    Write-ColorOutput "  ║  ██╔════╝ ██╔════╝██╔════╝██║ ██╔╝   ║" "Blue"
    Write-ColorOutput "  ║  ██║  ███╗█████╗  █████╗  █████╔╝    ║" "Blue"
    Write-ColorOutput "  ║  ██║   ██║██╔══╝  ██╔══╝  ██╔═██╗    ║" "Blue"
    Write-ColorOutput "  ║  ╚██████╔╝███████╗███████╗██║  ██╗   ║" "Blue"
    Write-ColorOutput "  ║   ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝   ║" "Blue"
    Write-ColorOutput "  ║           CODE                        ║" "Blue"
    Write-ColorOutput "  ║                                       ║" "Blue"
    Write-ColorOutput "  ║   Resumable AI Agent for Developers   ║" "Blue"
    Write-ColorOutput "  ║                                       ║" "Blue"
    Write-ColorOutput "  ╚═══════════════════════════════════════╝" "Blue"
    Write-Host ""
}

function Test-Python {
    Write-Info "Checking Python installation..."

    $pythonCmd = $null

    # Try python3 first
    try {
        $null = Get-Command python3 -ErrorAction Stop
        $pythonCmd = "python3"
    }
    catch {
        # Try python
        try {
            $null = Get-Command python -ErrorAction Stop
            $pythonCmd = "python"
        }
        catch {
            Write-Error "Python is not installed. Please install Python $PythonMinVersion or higher."
        }
    }

    # Check version
    $versionOutput = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $installedVersion = [version]$versionOutput

    if ($installedVersion -lt $PythonMinVersion) {
        Write-Error "Python $versionOutput found, but $PythonMinVersion or higher is required."
    }

    Write-Success "Found Python $versionOutput"
    return $pythonCmd
}

function Test-Pip {
    param([string]$PythonCmd)

    Write-Info "Checking pip installation..."

    try {
        & $PythonCmd -m pip --version | Out-Null
        Write-Success "pip is available"
        return "$PythonCmd -m pip"
    }
    catch {
        Write-Warning "pip not found. Installing pip..."
        & $PythonCmd -m ensurepip --upgrade
        return "$PythonCmd -m pip"
    }
}

function Install-GeekCode {
    param(
        [string]$PipCmd,
        [string]$Version
    )

    Write-Info "Installing GeekCode..."

    if ($Version -eq "latest") {
        Invoke-Expression "$PipCmd install --upgrade geekcode"
    }
    else {
        Invoke-Expression "$PipCmd install geekcode==$Version"
    }

    Write-Success "GeekCode installed successfully"
}

function Install-FromSource {
    param(
        [string]$PipCmd,
        [string]$SourcePath
    )

    Write-Info "Installing GeekCode from source..."

    if (Test-Path $SourcePath) {
        Push-Location $SourcePath
        Invoke-Expression "$PipCmd install -e .[dev]"
        Pop-Location
        Write-Success "GeekCode installed from source"
    }
    else {
        Write-Error "Source directory not found: $SourcePath"
    }
}

function Initialize-Config {
    Write-Info "Setting up configuration..."

    if (-not (Test-Path $GeekCodeConfigDir)) {
        New-Item -ItemType Directory -Path $GeekCodeConfigDir -Force | Out-Null
    }

    $configPath = Join-Path $GeekCodeConfigDir "config.yaml"

    if (-not (Test-Path $configPath)) {
        $configContent = @"
# GeekCode Configuration
# See https://github.com/geekcode/geekcode for documentation

providers:
  openai:
    api_key: null  # Set via OPENAI_API_KEY env var
    models:
      - gpt-4
      - gpt-4-turbo
      - gpt-3.5-turbo
    default_model: gpt-4
    enabled: true

  anthropic:
    api_key: null  # Set via ANTHROPIC_API_KEY env var
    models:
      - claude-3-opus
      - claude-3-sonnet
      - claude-3-haiku
    default_model: claude-3-sonnet
    enabled: true

  google:
    api_key: null  # Set via GOOGLE_API_KEY env var
    models:
      - gemini-pro
      - gemini-pro-vision
    default_model: gemini-pro
    enabled: true

  ollama:
    api_base: http://localhost:11434
    models:
      - llama2
      - codellama
      - mistral
    default_model: llama2
    enabled: false

agent:
  model: null  # Uses provider default
  max_tokens: 4096
  temperature: 0.7
  timeout: 120
  retry_count: 3
"@
        Set-Content -Path $configPath -Value $configContent
        Write-Success "Created default configuration at $configPath"
    }
    else {
        Write-Info "Configuration already exists at $configPath"
    }
}

function Test-Installation {
    Write-Info "Verifying installation..."

    try {
        $version = & geekcode --version 2>&1
        Write-Success "GeekCode is installed: $version"
    }
    catch {
        # Try to find in Python scripts directory
        $pythonScripts = Join-Path $env:APPDATA "Python\Python*\Scripts"
        $geekcodePath = Get-ChildItem -Path $pythonScripts -Filter "geekcode.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

        if ($geekcodePath) {
            Write-Success "GeekCode is installed at: $($geekcodePath.FullName)"
            Write-Warning "You may need to add the Scripts directory to your PATH"
        }
        else {
            Write-Error "Installation verification failed. geekcode command not found."
        }
    }
}

function Show-Instructions {
    Write-Host ""
    Write-ColorOutput "═══════════════════════════════════════════════════════" "Green"
    Write-ColorOutput "  GeekCode has been installed successfully!" "Green"
    Write-ColorOutput "═══════════════════════════════════════════════════════" "Green"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "  1. Set up your API keys:"
    Write-Host '     $env:OPENAI_API_KEY = "your-key-here"'
    Write-Host '     $env:ANTHROPIC_API_KEY = "your-key-here"'
    Write-Host ""
    Write-Host "  2. Initialize GeekCode in your project:"
    Write-Host "     cd your-project"
    Write-Host "     geekcode init"
    Write-Host ""
    Write-Host "  3. Run your first task:"
    Write-Host '     geekcode run "Explain this codebase"'
    Write-Host ""
    Write-Host "  For more information, visit:"
    Write-Host "  https://github.com/geekcode/geekcode"
    Write-Host ""
}

function Show-Help {
    Write-Host "GeekCode Installation Script for Windows"
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Version VERSION     Install specific version (default: latest)"
    Write-Host "  -FromSource PATH     Install from source directory"
    Write-Host "  -Help                Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\install.ps1"
    Write-Host "  .\install.ps1 -Version 0.1.0"
    Write-Host "  .\install.ps1 -FromSource C:\path\to\geekcode"
}

# Main
function Main {
    if ($Help) {
        Show-Help
        exit 0
    }

    Show-Banner

    $pythonCmd = Test-Python
    $pipCmd = Test-Pip -PythonCmd $pythonCmd

    if ($FromSource) {
        Install-FromSource -PipCmd $pipCmd -SourcePath $FromSource
    }
    else {
        Install-GeekCode -PipCmd $pipCmd -Version $Version
    }

    Initialize-Config
    Test-Installation
    Show-Instructions
}

Main
