<# 
.SYNOPSIS
  Reads vision17_data.json conversation and writes a more readable .txt output.

.DESCRIPTION
  This script takes an input JSON file structured like:
  {
    "messages": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
      ...
    ]
  }
  and converts each message into a human-friendly text format, outputting to
  a .txt file so you can view it easily.

.EXAMPLE
  .\convert_vision17_data.ps1 -InputPath ".\vision17_data.json" -OutputPath ".\formatted_vision17_data.txt"
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory=$true, HelpMessage="Path to the input JSON file")]
    [string]$InputPath,

    [Parameter(Mandatory=$true, HelpMessage="Path to the output text file")]
    [string]$OutputPath
)

# Try importing the JSON data
try {
    Write-Verbose "Reading file: $InputPath"
    $jsonData = Get-Content -Path $InputPath -Raw | ConvertFrom-Json
} catch {
    Write-Error "Error reading/parsing JSON file: $_"
    return
}

# If the JSON doesn't have 'messages', we can't proceed
if (-not $jsonData.messages) {
    Write-Error "No 'messages' property found in the input JSON. Aborting."
    return
}

# Prepare a list to hold lines for the text file
$outputLines = New-Object System.Collections.Generic.List[string]

# Loop through each message in the conversation
foreach ($msg in $jsonData.messages) {

    # We'll label the lines by role, e.g.: "User: Hello!"
    switch -Wildcard ($msg.role) {
        "user" {
            $roleLabel = "User"
        }
        "assistant" {
            $roleLabel = "Assistant"
        }
        default {
            $roleLabel = $msg.role  # If there's any unexpected role, just show it
        }
    }

    # Fix: Properly format roleLabel with PowerShell syntax
    $outputLines.Add("${roleLabel}: $($msg.content)")
    $outputLines.Add("")  # Blank line for spacing
}

# Write the final text lines to the output file
try {
    Write-Verbose "Writing formatted conversation to: $OutputPath"
    $outputLines | Out-File -Encoding UTF8 $OutputPath
    Write-Host "Formatted conversation saved to: $OutputPath"
} catch {
    Write-Error "Error writing formatted data: $_"
}
