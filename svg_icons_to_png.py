#!/usr/bin/env python

# Convert SVG images to PNG images in desired sizes
# Usage: python svg_icons_to_png.py

import os

import cairosvg

svg_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "traffic_control",
    "static",
    "traffic_control",
    "svg",
    "traffic_sign_icons",
)
png_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "traffic_control",
    "static",
    "traffic_control",
    "png",
    "traffic_sign_icons",
)


def convert_svg_to_png():
    """Convert SVG images to PNG images in desired sizes"""
    sizes = [32, 64, 128, 256]

    for size in sizes:
        size_folder = os.path.join(png_folder, str(size))
        if not os.path.exists(size_folder):
            os.makedirs(size_folder)

    created = 0
    for filename in os.listdir(svg_folder):
        if filename.endswith(".svg"):
            svg_path = os.path.join(svg_folder, filename)

            for size in sizes:
                png_path = os.path.join(png_folder, str(size), f"{filename}.png")
                with open(svg_path, "rb") as svg_file:
                    cairosvg.svg2png(file_obj=svg_file, write_to=png_path, output_width=size, output_height=size)
                    created += 1

            print(f"Converted {filename} to PNGs")

    print(f"All SVG images converted to PNG. Created {created} files.")


def clean():
    """Remove all PNG files"""
    print("Cleaning PNG folder...")

    removed = 0
    if os.path.exists(png_folder):
        for root, dirs, files in os.walk(png_folder):
            for file in files:
                if file.endswith(".png"):
                    os.remove(os.path.join(root, file))
                    removed += 1

    print(f"Cleaning PNG folder completed. Removed {removed} files.")


if __name__ == "__main__":
    clean()
    convert_svg_to_png()
