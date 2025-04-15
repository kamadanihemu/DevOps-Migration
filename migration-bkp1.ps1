#!/usr/bin/env pwsh

# =========== Created with CLI version 1.10.0 ===========

function Exec {
    param (
        [scriptblock]$ScriptBlock
    )
    & @ScriptBlock
    if ($lastexitcode -ne 0) {
        exit $lastexitcode
    }
}

function ExecAndGetMigrationID {
    param (
        [scriptblock]$ScriptBlock
    )
    $MigrationID = & @ScriptBlock | ForEach-Object {
        Write-Host $_
        $_
    } | Select-String -Pattern "\(ID: (.+)\)" | ForEach-Object { $_.matches.groups[1] }
    return $MigrationID
}

function ExecBatch {
    param (
        [scriptblock[]]$ScriptBlocks
    )
    $Global:LastBatchFailures = 0
    foreach ($ScriptBlock in $ScriptBlocks)
    {
        & @ScriptBlock
        if ($lastexitcode -ne 0) {
            $Global:LastBatchFailures++
        }
    }
}

if (-not $env:ADO_PAT) {
    Write-Error "ADO_PAT environment variable must be set to a valid Azure DevOps Personal Access Token with the appropriate scopes. For more information see https://docs.github.com/en/migrations/using-github-enterprise-importer/preparing-to-migrate-with-github-enterprise-importer/managing-access-for-github-enterprise-importer#personal-access-tokens-for-azure-devops"
    exit 1
} else {
    Write-Host "ADO_PAT environment variable is set and will be used to authenticate to Azure DevOps."
}

if (-not $env:GH_PAT) {
    Write-Error "GH_PAT environment variable must be set to a valid GitHub Personal Access Token with the appropriate scopes. For more information see https://docs.github.com/en/migrations/using-github-enterprise-importer/preparing-to-migrate-with-github-enterprise-importer/managing-access-for-github-enterprise-importer#creating-a-personal-access-token-for-github-enterprise-importer"
    exit 1
} else {
    Write-Host "GH_PAT environment variable is set and will be used to authenticate to GitHub."
}

$Succeeded = 0
$Failed = 0
$RepoMigrations = [ordered]@{}

# =========== Queueing migration for Organization: Shiva170296 ===========

# === Queueing repo migrations for Team Project: Shiva170296/newtestrepo ===

$MigrationID = ExecAndGetMigrationID { gh ado2gh migrate-repo --ado-org "Shiva170296" --ado-team-project "newtestrepo" --ado-repo "newtestrepo" --github-org "shivallamorg" --github-repo "newtestrepo-newtestrepo" --queue-only --target-repo-visibility private }
$RepoMigrations["Shiva170296/newtestrepo-newtestrepo"] = $MigrationID

# === Queueing repo migrations for Team Project: Shiva170296/ProjectPersonal ===

$MigrationID = ExecAndGetMigrationID { gh ado2gh migrate-repo --ado-org "Shiva170296" --ado-team-project "ProjectPersonal" --ado-repo "ProjectPersonal" --github-org "shivallamorg" --github-repo "ProjectPersonal-ProjectPersonal" --queue-only --target-repo-visibility private }
$RepoMigrations["Shiva170296/ProjectPersonal-ProjectPersonal"] = $MigrationID

# =========== Waiting for all migrations to finish for Organization: Shiva170296 ===========

# === Waiting for repo migration to finish for Team Project: newtestrepo and Repo: newtestrepo. Will then complete the below post migration steps. ===
$CanExecuteBatch = $false
if ($null -ne $RepoMigrations["Shiva170296/newtestrepo-newtestrepo"]) {
    gh ado2gh wait-for-migration --migration-id $RepoMigrations["Shiva170296/newtestrepo-newtestrepo"]
    $CanExecuteBatch = ($lastexitcode -eq 0)
}
if ($CanExecuteBatch) {
    $Succeeded++
} else {
    $Failed++
}

# === Waiting for repo migration to finish for Team Project: ProjectPersonal and Repo: ProjectPersonal. Will then complete the below post migration steps. ===
$CanExecuteBatch = $false
if ($null -ne $RepoMigrations["Shiva170296/ProjectPersonal-ProjectPersonal"]) {
    gh ado2gh wait-for-migration --migration-id $RepoMigrations["Shiva170296/ProjectPersonal-ProjectPersonal"]
    $CanExecuteBatch = ($lastexitcode -eq 0)
}
if ($CanExecuteBatch) {
    $Succeeded++
} else {
    $Failed++
}

Write-Host =============== Summary ===============
Write-Host Total number of successful migrations: $Succeeded
Write-Host Total number of failed migrations: $Failed

if ($Failed -ne 0) {
    exit 1
}


