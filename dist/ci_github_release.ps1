param([string]$token,[string]$tag,[string]$name,[string]$descr,[string]$user,[string]$project,[string]$file)

# Simplified version of the Release Uploader in https://github.com/Maximus5/Scripts

$auth = @{"Authorization"="token $token"}
$files = $file.Split("|")

function UploadAsset([int]$req_id,[string]$fullpath)
{
  $filename = Split-Path $fullpath -Leaf
  $content_type = "application/octet-stream"
  $req_arg = $auth + @{"Content-Type"=$content_type; "name"=$filename;}
  $req_arg_js = ConvertTo-Json $req_arg
  $body = [System.IO.File]::ReadAllBytes($fullpath)

  Write-Host " - Uploading to GitHub Releases.."
  $req = Invoke-WebRequest -UseBasicParsing -Headers $req_arg -Method POST -Body $body -Uri https://uploads.github.com/repos/$user/$project/releases/$req_id/assets?name=$filename

  Write-Host " - Upload done"
  if (($req -eq $null) -Or ($req.StatusCode -ne 201)) {
    $req
    $host.SetShouldExit(101)
    exit
  }
  $req_js = ConvertFrom-Json $req.Content
  Write-Host (" - URL: " + $req_js.browser_download_url)
}

function FindAsset([int]$req_id,[string]$fullpath)
{
  $filename = Split-Path $fullpath -Leaf
  $asset_id = 0
  $req = Invoke-WebRequest -UseBasicParsing -Headers $auth -Uri https://api.github.com/repos/$user/$project/releases/$req_id/assets
  if ($req -eq $null) {
    return 0
  }
  $req_js = ConvertFrom-Json $req.Content
  $req_js | where {$_.name -eq $filename} | foreach {
    $asset_id = $_.id
    Write-Host "Asset $filename was already uploaded, id: $asset_id"
    Write-Host (" - URL: " + $_.browser_download_url)
  }
  return $asset_id
}

function FindRelease([string]$tag_name)
{
  $req_id = 0
  $req = Invoke-WebRequest -UseBasicParsing -Headers $auth -Uri https://api.github.com/repos/$user/$project/releases
  if ($req -eq $null) {
    return 0
  }
  $req_js = ConvertFrom-Json $req.Content
  $req_js | where {$_.tag_name -eq $tag_name} | foreach {
    $req_id = $_.id
    Write-Host ("Release found, upload_url=" + $_.upload_url)
  }
  return $req_id
}

function CreateRelease([string]$tag,[string]$name,[string]$descr)
{
  $req_arg = @{ `
    "tag_name"=$tag; `
    "name"=$name; `
    "body"=$descr; `
    "draft"=$TRUE; `
    "prerelease"=$FALSE
  }

  $req_arg_js = ConvertTo-Json $req_arg

  $req = Invoke-WebRequest -UseBasicParsing -Headers $auth -Method POST -Body $req_arg_js -Uri https://api.github.com/repos/$user/$project/releases
  if ($req -ne $null)
  {
    $req_js = ConvertFrom-Json $req.Content
    return $req_js.id
  }

  $host.SetShouldExit(101)
  exit
}

# Fix default SecurityProtocol = "Ssl3, Tls"
[Net.ServicePointManager]::SecurityProtocol = "tls12, tls11, tls"

Write-Host "Trying to find release $tag"
$req_id = FindRelease $tag
if ($req_id -ne 0) {
  Write-Host "Release already created, id: $req_id"
} else {
  $req_id = CreateRelease $tag $name $descr
  Write-Host "Release created, id: $req_id"
}

$files | foreach {
  $asset_id = FindAsset $req_id $_
  if ($asset_id -ne 0) {
    Write-Host "Asset $_ was already uploaded, id: $asset_id. Skipping.."
  } else {
    UploadAsset $req_id $_
  }
}
