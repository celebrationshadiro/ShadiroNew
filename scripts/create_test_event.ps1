# Script to create a test event and display it

# Configuration
$API_URL = "http://localhost:8000/api"

# Step 1: Register/Login to get JWT token
Write-Host "Step 1: Creating test user and getting JWT token..." -ForegroundColor Cyan

$loginData = @{
    email = "testuser@example.com"
    password = "TestPassword123!"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$API_URL/auth/login" -Method POST -Body $loginData -ContentType "application/json" -ErrorAction Stop
    $token = $loginResponse.data.access_token
    Write-Host "✓ Login successful! Token: $($token.Substring(0, 20))..." -ForegroundColor Green
} catch {
    Write-Host "Login failed. Attempting registration first..." -ForegroundColor Yellow
    
    $registerData = @{
        email = "testuser@example.com"
        password = "TestPassword123!"
        name = "Test User"
        phone = "9999999999"
        role = "user"
    } | ConvertTo-Json
    
    try {
        $registerResponse = Invoke-RestMethod -Uri "$API_URL/auth/register" -Method POST -Body $registerData -ContentType "application/json"
        $token = $registerResponse.data.access_token
        Write-Host "✓ Registration successful!" -ForegroundColor Green
    } catch {
        Write-Host "✗ Registration failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Create an event
Write-Host "`nStep 2: Creating a test event..." -ForegroundColor Cyan

$eventDate = (Get-Date).AddDays(30).ToString("yyyy-MM-dd")

$eventData = @{
    event_type = "wedding"
    title = "Dream Wedding 2026"
    date = $eventDate
    location = "Mumbai, Maharashtra"
    guest_count = 150
    budget_min = 500000
    budget_max = 1500000
    description = "Beautiful wedding celebration with family and friends"
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

try {
    $eventResponse = Invoke-RestMethod -Uri "$API_URL/events" -Method POST -Body $eventData -Headers $headers
    $eventId = $eventResponse.data.id
    Write-Host "✓ Event created successfully!" -ForegroundColor Green
    Write-Host "  Event ID: $eventId" -ForegroundColor Yellow
    Write-Host "  Title: $($eventResponse.data.title)"
    Write-Host "  Date: $($eventResponse.data.date)"
    Write-Host "  Budget: ₹$($eventResponse.data.budget_min) - ₹$($eventResponse.data.budget_max)"
} catch {
    Write-Host "✗ Event creation failed: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Verify by fetching all events
Write-Host "`nStep 3: Fetching all your events..." -ForegroundColor Cyan

try {
    $eventsResponse = Invoke-RestMethod -Uri "$API_URL/events" -Method GET -Headers $headers
    Write-Host "✓ Events retrieved successfully!" -ForegroundColor Green
    Write-Host "  Total events: $($eventsResponse.data.Count)" -ForegroundColor Yellow
    
    foreach ($event in $eventsResponse.data) {
        Write-Host "`n  📅 Event: $($event.title)"
        Write-Host "     Date: $($event.date)"
        Write-Host "     Type: $($event.event_type)"
        Write-Host "     Location: $($event.location)"
        Write-Host "     ID: $($event.id)"
    }
} catch {
    Write-Host "✗ Failed to fetch events: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n✨ Done! Now you can go to the checkout page and select this event." -ForegroundColor Green
Write-Host "Credentials: testuser@example.com / TestPassword123!" -ForegroundColor Cyan
