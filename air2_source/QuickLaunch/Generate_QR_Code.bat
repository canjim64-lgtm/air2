@echo off
title AirOne Professional v4.0 - QR Code Generator
color 0B
echo ========================================================================
echo    AirOne Professional v4.0 - QR Code Generator
echo ========================================================================
echo.
echo This tool generates QR codes for:
echo   - Passwords
echo   - URLs
echo   - WiFi credentials
echo   - Contact information (vCard)
echo   - Plain text
echo.
echo Note: Requires qrcode library
echo Install: pip install qrcode[pil]
echo.
set /p data_type="Enter data type (password/url/wifi/text): "

if /i "%data_type%"=="password" (
    set /p username="Enter username: "
    set /p password="Enter password: "
    python -c "from src.qr_generator import generate_password_qr; qr = generate_password_qr('%username%', '%password%'); print(f'QR code saved to: {qr}' if qr else 'Failed to generate QR code')"
) else if /i "%data_type%"=="url" (
    set /p url="Enter URL: "
    python -c "from src.qr_generator import generate_qr_code; qr = generate_qr_code('%url%'); print(f'QR code saved to: {qr}' if qr else 'Failed to generate QR code')"
) else if /i "%data_type%"=="wifi" (
    set /p ssid="Enter WiFi SSID: "
    set /p password="Enter WiFi password: "
    python -c "from src.qr_generator import QRCodeGenerator; g = QRCodeGenerator(); qr = g.generate_wifi_qr('%ssid%', '%password%'); print(f'QR code saved to: {qr}' if qr else 'Failed to generate QR code')"
) else (
    set /p text="Enter text: "
    python -c "from src.qr_generator import generate_qr_code; qr = generate_qr_code('%text%'); print(f'QR code saved to: {qr}' if qr else 'Failed to generate QR code')"
)

echo.
pause
