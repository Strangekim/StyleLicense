#!/usr/bin/env python3
"""
Image Optimization Script

Converts PNG images to WebP format with quality optimization.
Significantly reduces file size while maintaining visual quality.
"""

import os
from pathlib import Path
from PIL import Image

def optimize_image(input_path, output_path, quality=85):
    """
    Convert image to WebP format with specified quality.

    Args:
        input_path: Path to input PNG file
        output_path: Path to output WebP file
        quality: WebP quality (0-100, default 85)

    Returns:
        tuple: (original_size, new_size, reduction_percent)
    """
    # Get original file size
    original_size = os.path.getsize(input_path)

    # Open and convert image
    img = Image.open(input_path)

    # Convert RGBA to RGB if necessary (WebP supports alpha, but check)
    if img.mode == 'RGBA':
        # Keep alpha channel for WebP
        img.save(output_path, 'WEBP', quality=quality, method=6)
    else:
        img.save(output_path, 'WEBP', quality=quality, method=6)

    # Get new file size
    new_size = os.path.getsize(output_path)

    # Calculate reduction
    reduction = ((original_size - new_size) / original_size) * 100

    return original_size, new_size, reduction

def format_size(size_bytes):
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} GB"

def main():
    # Define paths
    script_dir = Path(__file__).parent
    assets_dir = script_dir.parent / 'src' / 'assets' / 'images'

    # Find all PNG files
    png_files = list(assets_dir.glob('*.png'))

    if not png_files:
        print("No PNG files found in assets/images/")
        return

    print(f"Found {len(png_files)} PNG files to optimize\n")

    total_original = 0
    total_new = 0

    for png_file in png_files:
        output_file = png_file.with_suffix('.webp')

        print(f"Optimizing: {png_file.name}")

        try:
            original_size, new_size, reduction = optimize_image(
                png_file,
                output_file,
                quality=85
            )

            total_original += original_size
            total_new += new_size

            print(f"  Original: {format_size(original_size)}")
            print(f"  Optimized: {format_size(new_size)}")
            print(f"  Reduction: {reduction:.1f}%")
            print(f"  Saved: {format_size(original_size - new_size)}\n")

        except Exception as e:
            print(f"  Error: {e}\n")

    # Summary
    total_reduction = ((total_original - total_new) / total_original) * 100
    print("=" * 50)
    print("Summary:")
    print(f"  Total original size: {format_size(total_original)}")
    print(f"  Total optimized size: {format_size(total_new)}")
    print(f"  Total reduction: {total_reduction:.1f}%")
    print(f"  Total saved: {format_size(total_original - total_new)}")
    print("=" * 50)

if __name__ == '__main__':
    main()
