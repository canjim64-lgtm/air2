"""
AirOne Professional v4.0 - QR Code Generator
Generate QR codes for passwords, URLs, and data
"""
# -*- coding: utf-8 -*-

import os
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """Generate QR codes for various data types"""
    
    def __init__(self, output_dir: str = "qrcodes"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.qrcode_available = False
        
        # Try to import QR code library
        try:
            import qrcode
            self.qrcode_available = True
            self.qrcode = qrcode
        except ImportError:
            logger.warning("qrcode library not available - install with: pip install qrcode[pil]")
    
    def generate_qr(self, data: str, filename: Optional[str] = None, 
                    size: int = 10, border: int = 4) -> Optional[str]:
        """
        Generate QR code for data
        
        Args:
            data: Data to encode in QR code
            filename: Output filename (auto-generated if None)
            size: Box size (pixels per module)
            border: Border size in modules
            
        Returns:
            Path to generated QR code file, or None if failed
        """
        if not self.qrcode_available:
            logger.error("QR code library not available")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_hash = hashlib.md5(data.encode()).hexdigest()[:8]
            filename = f"qrcode_{data_hash}_{timestamp}.png"
        
        filepath = self.output_dir / filename
        
        try:
            # Create QR code
            qr = self.qrcode.QRCode(
                version=1,
                error_correction=self.qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filepath)
            
            logger.info(f"QR code generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            return None
    
    def generate_password_qr(self, username: str, password: str) -> Optional[str]:
        """
        Generate QR code for password credentials
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Path to QR code file
        """
        # Format for password storage
        data = f"AIRONE_PASSWORD|{username}|{password}"
        filename = f"password_qr_{username}.png"
        
        return self.generate_qr(data, filename)
    
    def generate_wifi_qr(self, ssid: str, password: str, 
                        security: str = "WPA") -> Optional[str]:
        """
        Generate QR code for WiFi credentials
        
        Args:
            ssid: WiFi network name
            password: WiFi password
            security: Security type (WEP, WPA, WPA2, WPA3)
            
        Returns:
            Path to QR code file
        """
        # WiFi QR code format
        data = f"WIFI:T:{security};S:{ssid};P:{password};;"
        filename = f"wifi_qr_{ssid.replace(' ', '_')}.png"
        
        return self.generate_qr(data, filename)
    
    def generate_url_qr(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Generate QR code for URL
        
        Args:
            url: URL to encode
            filename: Output filename
            
        Returns:
            Path to QR code file
        """
        return self.generate_qr(url, filename)
    
    def generate_text_qr(self, text: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Generate QR code for plain text
        
        Args:
            text: Text to encode
            filename: Output filename
            
        Returns:
            Path to QR code file
        """
        return self.generate_qr(text, filename)
    
    def generate_vcard_qr(self, name: str, phone: str, email: str,
                         organization: str = "", title: str = "") -> Optional[str]:
        """
        Generate QR code for vCard contact
        
        Args:
            name: Full name
            phone: Phone number
            email: Email address
            organization: Organization/company
            title: Job title
            
        Returns:
            Path to QR code file
        """
        vcard = f"BEGIN:VCARD\nVERSION:3.0\nN:{name}\nFN:{name}"
        if organization:
            vcard += f"\nORG:{organization}"
        if title:
            vcard += f"\nTITLE:{title}"
        if phone:
            vcard += f"\nTEL:{phone}"
        if email:
            vcard += f"\nEMAIL:{email}"
        vcard += "\nEND:VCARD"
        
        filename = f"contact_qr_{name.replace(' ', '_')}.png"
        return self.generate_qr(vcard, filename)


def generate_qr_code(data: str, output_file: Optional[str] = None) -> Optional[str]:
    """Quick function to generate QR code"""
    generator = QRCodeGenerator()
    return generator.generate_qr(data, output_file)


def generate_password_qr(username: str, password: str) -> Optional[str]:
    """Quick function to generate password QR code"""
    generator = QRCodeGenerator()
    return generator.generate_password_qr(username, password)


if __name__ == "__main__":
    # Test QR code generator
    print("="*70)
    print("  AirOne Professional v4.0 - QR Code Generator Test")
    print("="*70)
    print()
    
    generator = QRCodeGenerator()
    
    if generator.qrcode_available:
        print("QR code library available!")
        print()
        
        # Test 1: Generate text QR
        print("[Test 1] Generate text QR code...")
        qr1 = generator.generate_text_qr("Hello, AirOne Professional v4.0!")
        if qr1:
            print(f"  [OK] Generated: {qr1}")
        else:
            print("  [FAIL] Generation failed")
        print()
        
        # Test 2: Generate URL QR
        print("[Test 2] Generate URL QR code...")
        qr2 = generator.generate_url_qr("https://airone.professional")
        if qr2:
            print(f"  [OK] Generated: {qr2}")
        else:
            print("  [FAIL] Generation failed")
        print()
        
        # Test 3: Generate password QR
        print("[Test 3] Generate password QR code...")
        qr3 = generator.generate_password_qr("test_user", "test_password_123")
        if qr3:
            print(f"  [OK] Generated: {qr3}")
        else:
            print("  [FAIL] Generation failed")
        print()
        
        print("="*70)
        print("  QR Code Generator Test Complete")
        print("="*70)
        print()
        print(f"QR codes saved to: {generator.output_dir.absolute()}")
        print()
    else:
        print("QR code library NOT available.")
        print()
        print("To enable QR code generation, install:")
        print("  pip install qrcode[pil]")
        print()
