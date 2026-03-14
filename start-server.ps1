# 简单的HTTP服务器，确保正确处理UTF-8编码
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add('http://localhost:8080/')
$listener.Start()
Write-Host 'Server running at http://localhost:8080' -ForegroundColor Green

while ($listener.IsListening) {
    try {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        
        $filePath = $request.Url.LocalPath
        
        if ($filePath -eq '/') {
            $filePath = '/login.html'
        }
        
        $fileName = $filePath.Substring(1)
        if ([string]::IsNullOrEmpty($fileName)) {
            $fileName = 'index.html'
        }
        $fullPath = Join-Path -Path (Get-Location).Path -ChildPath $fileName
        
        if (Test-Path -Path $fullPath -PathType Leaf) {
            $content = Get-Content -Path $fullPath -Raw -Encoding UTF8
            
            $extension = [System.IO.Path]::GetExtension($fullPath).ToLower()
            switch ($extension) {
                '.html' { $response.ContentType = 'text/html; charset=utf-8' }
                '.css' { $response.ContentType = 'text/css; charset=utf-8' }
                '.js' { $response.ContentType = 'application/javascript; charset=utf-8' }
                default { $response.ContentType = 'application/octet-stream' }
            }
            
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($content)
            $response.ContentLength64 = $buffer.Length
            
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        } else {
            $response.StatusCode = 404
            $response.ContentType = 'text/html; charset=utf-8'
            $errorContent = '<html><body><h1>404 Not Found</h1><p>The requested resource was not found.</p></body></html>'
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($errorContent)
            $response.ContentLength64 = $buffer.Length
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        }
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        if ($response) {
            $response.Close()
        }
    }
}

$listener.Stop()
$listener.Close()