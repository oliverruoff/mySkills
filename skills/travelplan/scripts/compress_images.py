#!/usr/bin/env python3
"""
Komprimiert alle Bilder in einem Verzeichnis für die PDF-Einbettung.
Skaliert auf max 1200px Breite, JPEG Qualität 85%.

Usage:
    python3 compress_images.py <image_dir>
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow nicht installiert. Bitte: pip install Pillow")
    sys.exit(1)

MAX_WIDTH = 1200
QUALITY = 85


def compress_image(path):
    """Komprimiert ein einzelnes Bild."""
    try:
        img = Image.open(path)
        # Convert to RGB if necessary (e.g. PNG with transparency)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Resize if too wide
        w, h = img.size
        if w > MAX_WIDTH:
            ratio = MAX_WIDTH / w
            new_size = (MAX_WIDTH, int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        # Save as JPEG with compression
        output_path = str(path)
        if not output_path.lower().endswith(".jpg"):
            output_path = os.path.splitext(output_path)[0] + ".jpg"
            if output_path != str(path):
                os.remove(path)  # remove original non-jpg
        
        img.save(output_path, "JPEG", quality=QUALITY, optimize=True)
        return True
    except Exception as e:
        print(f"Fehler bei {path}: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compress_images.py <image_dir>")
        sys.exit(1)
    
    image_dir = sys.argv[1]
    total = 0
    compressed = 0
    
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif"):
        for path in Path(image_dir).glob(ext):
            total += 1
            if compress_image(path):
                compressed += 1
    
    print(f"{compressed}/{total} Bilder komprimiert.")


if __name__ == "__main__":
    main()
