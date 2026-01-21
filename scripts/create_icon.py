#!/usr/bin/env python3
"""
Create application icon for Docx MCP Server Launcher
Design: Document icon with gear/server symbol
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(output_path="resources/icon.ico", sizes=[16, 32, 48, 64, 128, 256]):
    """Create a multi-resolution .ico file"""

    images = []

    for size in sizes:
        # Create new image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Scale-dependent parameters
        scale = size / 256.0

        # Colors
        bg_color = (41, 128, 185, 255)      # Professional blue
        doc_color = (255, 255, 255, 255)    # White document
        accent_color = (231, 76, 60, 255)   # Red accent for gear
        shadow_color = (0, 0, 0, 60)        # Subtle shadow

        # Draw shadow
        shadow_offset = int(4 * scale)
        draw.rounded_rectangle(
            [shadow_offset, shadow_offset, size - shadow_offset, size - shadow_offset],
            radius=int(16 * scale),
            fill=shadow_color
        )

        # Draw background circle
        margin = int(8 * scale)
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=bg_color
        )

        # Draw document icon
        doc_margin = int(48 * scale)
        doc_width = size - doc_margin * 2
        doc_height = int(doc_width * 1.3)

        doc_x = (size - doc_width) // 2
        doc_y = int(32 * scale)

        # Document body
        draw.rounded_rectangle(
            [doc_x, doc_y, doc_x + doc_width, doc_y + doc_height],
            radius=int(8 * scale),
            fill=doc_color
        )

        # Document lines (text representation)
        line_margin = int(16 * scale)
        line_height = int(6 * scale)
        line_spacing = int(12 * scale)

        for i in range(3):
            y = doc_y + int(30 * scale) + i * line_spacing
            if y + line_height < doc_y + doc_height - line_margin:
                draw.rounded_rectangle(
                    [
                        doc_x + line_margin,
                        y,
                        doc_x + doc_width - line_margin,
                        y + line_height
                    ],
                    radius=int(2 * scale),
                    fill=bg_color
                )

        # Draw gear icon (bottom right) to represent server/automation
        gear_size = int(56 * scale)
        gear_x = size - int(48 * scale)
        gear_y = size - int(48 * scale)

        # Gear background circle
        gear_bg_size = int(72 * scale)
        draw.ellipse(
            [
                gear_x - gear_bg_size // 2,
                gear_y - gear_bg_size // 2,
                gear_x + gear_bg_size // 2,
                gear_y + gear_bg_size // 2
            ],
            fill=accent_color
        )

        # Simple gear representation (circle with center hole)
        draw.ellipse(
            [
                gear_x - gear_size // 2,
                gear_y - gear_size // 2,
                gear_x + gear_size // 2,
                gear_y + gear_size // 2
            ],
            fill=(255, 255, 255, 255)
        )

        # Gear center hole
        center_size = int(20 * scale)
        draw.ellipse(
            [
                gear_x - center_size // 2,
                gear_y - center_size // 2,
                gear_x + center_size // 2,
                gear_y + center_size // 2
            ],
            fill=accent_color
        )

        # Add gear teeth (simplified)
        teeth_count = 6
        teeth_length = int(12 * scale)
        teeth_width = int(8 * scale)

        import math
        for i in range(teeth_count):
            angle = (2 * math.pi * i) / teeth_count
            x1 = gear_x + int((gear_size // 2) * math.cos(angle))
            y1 = gear_y + int((gear_size // 2) * math.sin(angle))
            x2 = gear_x + int((gear_size // 2 + teeth_length) * math.cos(angle))
            y2 = gear_y + int((gear_size // 2 + teeth_length) * math.sin(angle))

            draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 255), width=teeth_width)

        images.append(img)

    # Save as .ico
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )

    print(f"✅ Icon created: {output_path}")
    print(f"   Sizes: {', '.join([f'{s}x{s}' for s in sizes])}")

if __name__ == "__main__":
    # Ensure resources directory exists
    os.makedirs("resources", exist_ok=True)
    create_icon()
