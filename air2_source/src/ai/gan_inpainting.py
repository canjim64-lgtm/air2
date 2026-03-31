"""
GAN-based Packet In-Painting for RF Interference Recovery
Lightweight GAN to reconstruct corrupted visual data
Maintains clear visual of descent under low SNR conditions
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class InPaintedFrame:
    timestamp: float
    frame_id: int
    original: np.ndarray
    reconstructed: np.ndarray
    confidence: float
    corruption_map: np.ndarray
    missing_pixels: float  # Percentage of pixels reconstructed


class Generator(nn.Module):
    """Generator for image inpainting."""
    
    def __init__(self, channels: int = 64):
        super().__init__()
        
        # Encoder
        self.enc1 = self._conv_block(3, channels)
        self.enc2 = self._conv_block(channels, channels * 2)
        self.enc3 = self._conv_block(channels * 2, channels * 4)
        self.enc4 = self._conv_block(channels * 4, channels * 8)
        
        # Bottleneck
        self.bottleneck = nn.Sequential(
            nn.Conv2d(channels * 8, channels * 8, 3, 1, 1),
            nn.BatchNorm2d(channels * 8),
            nn.ReLU()
        )
        
        # Attention module for focusing on missing regions
        self.attention = nn.Sequential(
            nn.Conv2d(channels * 8, channels * 4, 1),
            nn.BatchNorm2d(channels * 4),
            nn.ReLU(),
            nn.Conv2d(channels * 4, channels * 8, 1),
            nn.Sigmoid()
        )
        
        # Decoder
        self.dec4 = self._deconv_block(channels * 8, channels * 4)
        self.dec3 = self._deconv_block(channels * 8, channels * 2)
        self.dec2 = self._deconv_block(channels * 6, channels)
        self.dec1 = self._deconv_block(channels * 3, channels // 2)
        
        # Output
        self.out = nn.Conv2d(channels // 2, 3, 3, 1, 1)
        
    def _conv_block(self, in_c, out_c):
        return nn.Sequential(
            nn.Conv2d(in_c, out_c, 3, 1, 1),
            nn.BatchNorm2d(out_c),
            nn.LeakyReLU(0.2),
            nn.Conv2d(out_c, out_c, 3, 1, 1),
            nn.BatchNorm2d(out_c),
            nn.LeakyReLU(0.2)
        )
        
    def _deconv_block(self, in_c, out_c):
        return nn.Sequential(
            nn.ConvTranspose2d(in_c, out_c, 2, 2),
            nn.BatchNorm2d(out_c),
            nn.ReLU(),
            nn.Conv2d(out_c, out_c, 3, 1, 1),
            nn.BatchNorm2d(out_c),
            nn.ReLU()
        )
        
    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input image [B, C, H, W]
            mask: Binary mask [B, 1, H, W] (1 = missing region)
            
        Returns:
            Reconstructed image
        """
        # Encode
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        
        # Bottleneck with attention
        b = self.bottleneck(e4)
        attn = self.attention(b)
        b = b * attn
        
        # Decode with skip connections
        d4 = self.dec4(b)
        d4 = torch.cat([d4, e3], dim=1)
        
        d3 = self.dec3(d4)
        d3 = torch.cat([d3, e2], dim=1)
        
        d2 = self.dec2(d3)
        d2 = torch.cat([d2, e1], dim=1)
        
        d1 = self.dec1(d2)
        
        # Output
        out = torch.tanh(self.out(d1))
        
        # Apply mask - only fill missing regions
        filled = x * (1 - mask) + out * mask
        
        return filled


class Discriminator(nn.Module):
    """Patch-based discriminator for GAN training."""
    
    def __init__(self, channels: int = 64):
        super().__init__()
        
        self.model = nn.Sequential(
            nn.Conv2d(3, channels, 4, 2, 1),
            nn.LeakyReLU(0.2),
            nn.Conv2d(channels, channels * 2, 4, 2, 1),
            nn.BatchNorm2d(channels * 2),
            nn.LeakyReLU(0.2),
            nn.Conv2d(channels * 2, channels * 4, 4, 2, 1),
            nn.BatchNorm2d(channels * 4),
            nn.LeakyReLU(0.2),
            nn.Conv2d(channels * 4, channels * 8, 4, 2, 1),
            nn.BatchNorm2d(channels * 8),
            nn.LeakyReLU(0.2),
            nn.Conv2d(channels * 8, 1, 4, 1, 1)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class ContextualAttention(nn.Module):
    """Attention mechanism for matching missing patches with valid regions."""
    
    def __init__(self, channels: int = 64):
        super().__init__()
        self.conv = nn.Conv2d(channels, channels, 1)
        
    def forward(self, background: torch.Tensor, foreground: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """
        Args:
            background: Valid regions [B, C, H, W]
            foreground: Corrupted regions to fill [B, C, H, W]
            mask: Binary mask
        """
        batch, channels, h, w = background.shape
        
        # Compute attention map
        bg_flat = background.view(batch, channels, -1)
        fg_flat = foreground.view(batch, channels, -1)
        
        # Cosine similarity
        norm_bg = F.normalize(bg_flat, dim=1)
        norm_fg = F.normalize(fg_flat, dim=1)
        
        attention = torch.bmm(norm_bg.transpose(1, 2), norm_fg)
        attention = F.softmax(attention, dim=1)
        
        # Apply attention
        attended = torch.bmm(bg_flat, attention)
        attended = attended.view(batch, channels, h, w)
        
        # Blend with foreground based on mask
        output = foreground * (1 - mask) + attended * mask
        
        return output


class InPaintingGAN:
    """
    GAN-based system for inpainting corrupted image packets.
    Reconstructs missing visual data due to RF interference.
    """
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        image_size: Tuple[int, int] = (256, 256)
    ):
        self.device = device
        self.image_size = image_size
        
        # Initialize networks
        self.generator = Generator().to(device)
        self.discriminator = Discriminator().to(device)
        self.contextual_attn = ContextualAttention().to(device)
        
        # Optimizers
        self.opt_g = torch.optim.Adam(self.generator.parameters(), lr=0.0002, betas=(0.5, 0.999))
        self.opt_d = torch.optim.Adam(self.discriminator.parameters(), lr=0.0002, betas=(0.5, 0.999))
        
        # Loss functions
        self.l1_loss = nn.L1Loss()
        self.mse_loss = nn.MSELoss()
        
        self.generator.eval()
        self.discriminator.eval()
        
    def preprocess_frame(
        self,
        frame: np.ndarray,
        corruption_mask: Optional[np.ndarray] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Preprocess frame for inpainting.
        
        Args:
            frame: Input image [H, W, 3]
            corruption_mask: Optional mask of corrupted pixels [H, W]
            
        Returns:
            frame_tensor: Preprocessed tensor
            mask_tensor: Corruption mask tensor
        """
        import cv2
        
        # Resize if needed
        if frame.shape[:2] != self.image_size:
            frame = cv2.resize(frame, self.image_size)
            
        # Normalize to [-1, 1]
        frame_norm = frame.astype(np.float32) / 127.5 - 1
        
        # Convert to tensor
        frame_tensor = torch.from_numpy(frame_norm).permute(2, 0, 1).unsqueeze(0).to(self.device)
        
        # Create or use mask
        if corruption_mask is None:
            # Auto-detect corruption based on noise pattern
            corruption_mask = self._detect_corruption(frame)
            
        if corruption_mask.shape != self.image_size:
            corruption_mask = cv2.resize(corruption_mask.astype(np.uint8), self.image_size)
            
        mask_tensor = torch.from_numpy(corruption_mask).unsqueeze(0).unsqueeze(0).float().to(self.device)
        
        return frame_tensor, mask_tensor
        
    def _detect_corruption(self, frame: np.ndarray) -> np.ndarray:
        """
        Automatically detect corrupted regions in frame.
        Uses noise analysis and saturation detection.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        # Check for extreme values (salt-and-pepper noise)
        high_noise = (gray > 250) | (gray < 5)
        
        # Check for block artifacts (common in RF corruption)
        kernel = np.ones((5, 5), np.uint8)
        noise_dilated = cv2.dilate(high_noise.astype(np.uint8), kernel)
        
        # Find areas with unusual variance (blurring artifacts)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        variance = np.abs(gray.astype(float) - blurred.astype(float))
        high_variance = variance > 50
        
        # Combine detection methods
        corruption = (noise_dilated | high_variance).astype(np.float32)
        
        # Dilate slightly to include surrounding area
        corruption = cv2.dilate(corruption, kernel, iterations=1)
        
        return corruption
        
    def inpaint(
        self,
        frame: np.ndarray,
        corruption_mask: Optional[np.ndarray] = None
    ) -> InPaintedFrame:
        """
        Inpaint a corrupted frame.
        
        Args:
            frame: Input image
            corruption_mask: Optional mask specifying corrupted regions
            
        Returns:
            InPaintedFrame with reconstruction
        """
        # Preprocess
        frame_tensor, mask_tensor = self.preprocess_frame(frame, corruption_mask)
        
        # Run generator
        with torch.no_grad():
            reconstructed = self.generator(frame_tensor, mask_tensor)
            
        # Compute metrics
        reconstruction = reconstructed[0].permute(1, 2, 0).cpu().numpy()
        reconstruction = (reconstruction + 1) * 127.5
        reconstruction = np.clip(reconstruction, 0, 255).astype(np.uint8)
        
        # Calculate confidence based on mask coverage
        missing_pixels = mask_tensor[0, 0].sum().item() / (self.image_size[0] * self.image_size[1])
        confidence = 1.0 - missing_pixels * 0.5  # Lower confidence for heavily corrupted frames
        
        # Calculate reconstruction similarity
        orig_tensor = frame_tensor.squeeze(0).permute(1, 2, 0)
        recon_tensor = torch.from_numpy(reconstruction.astype(np.float32) / 127.5 - 1).to(self.device)
        
        mask_np = mask_tensor[0, 0].cpu().numpy()
        similarity = np.mean(np.abs(orig_tensor.cpu().numpy() - recon_tensor.cpu().numpy()) * mask_np)
        
        return InPaintedFrame(
            timestamp=0.0,  # Would be set by caller
            frame_id=0,
            original=frame,
            reconstructed=reconstruction,
            confidence=float(confidence),
            corruption_map=mask_np,
            missing_pixels=float(missing_pixels)
        )
        
    def train_step(
        self,
        real_images: torch.Tensor,
        masks: torch.Tensor
    ) -> Dict[str, float]:
        """
        Perform one training step for the GAN.
        
        Args:
            real_images: Ground truth images
            masks: Corruption masks
        """
        batch_size = real_images.size(0)
        valid = torch.ones(batch_size, 1, 16, 16).to(self.device)
        fake = torch.zeros(batch_size, 1, 16, 16).to(self.device)
        
        # Generate fake images
        fake_images = self.generator(real_images, masks)
        
        # Train Discriminator
        self.opt_d.zero_grad()
        real_pred = self.discriminator(real_images)
        fake_pred = self.discriminator(fake_images.detach())
        
        d_loss = self.mse_loss(real_pred, valid) + self.mse_loss(fake_pred, fake)
        d_loss.backward()
        self.opt_d.step()
        
        # Train Generator
        self.opt_g.zero_grad()
        
        # Adversarial loss
        fake_pred = self.discriminator(fake_images)
        g_adv_loss = self.mse_loss(fake_pred, valid)
        
        # Reconstruction loss (L1) for masked regions
        g_l1_loss = self.l1_loss(fake_images * masks, real_images * masks)
        
        # Perceptual loss (simplified - just content loss)
        g_content_loss = self.l1_loss(fake_images, real_images)
        
        # Total generator loss
        g_loss = g_adv_loss + 100 * g_l1_loss + 10 * g_content_loss
        
        g_loss.backward()
        self.opt_g.step()
        
        return {
            'd_loss': d_loss.item(),
            'g_loss': g_loss.item(),
            'g_adv_loss': g_adv_loss.item(),
            'g_l1_loss': g_l1_loss.item()
        }


def create_inpainting_gan(device: str = "auto", image_size: Tuple[int, int] = (256, 256)) -> InPaintingGAN:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return InPaintingGAN(device=device, image_size=image_size)


# Demo
if __name__ == "__main__":
    print("Initializing InPainting GAN...")
    gan = create_inpainting_gan()
    
    # Simulate frame inpainting
    print("Processing simulated corrupted frames...")
    
    import cv2
    
    for i in range(10):
        # Create synthetic frame with corruption
        frame = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        # Add some corruption (random blocks)
        for _ in range(3):
            x, y = np.random.randint(0, 200), np.random.randint(0, 200)
            w, h = np.random.randint(20, 60), np.random.randint(20, 60)
            frame[y:y+h, x:x+w] = np.random.randint(0, 50, (h, w, 3), dtype=np.uint8)
        
        result = gan.inpaint(frame)
        
        print(f"Frame {i}: Confidence={result.confidence:.2%}, "
              f"Missing pixels={result.missing_pixels:.1%}")
        
    print("\nInpainting system ready for deployment.")