"""Generate icon.ico from the SVG design using Pillow.

Run once: python generate_icon.py
Produces icon.ico with 16x16, 32x32, 48x48, and 256x256 sizes.
"""

from PIL import Image, ImageDraw


def draw_icon(size: int) -> Image.Image:
    """Draw the app icon at the given size, matching icon.svg."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size / 64  # scale factor from 64x64 base

    # Background rounded rect
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(12 * s), fill="#1a1a1a")

    # Left bar: x=14 y=16 w=8 h=32 rx=2
    draw.rounded_rectangle(
        [int(14 * s), int(16 * s), int(22 * s), int(48 * s)],
        radius=max(1, int(2 * s)),
        fill="#4caf50",
    )

    # Right bar: x=42 y=16 w=8 h=32 rx=2
    draw.rounded_rectangle(
        [int(42 * s), int(16 * s), int(50 * s), int(48 * s)],
        radius=max(1, int(2 * s)),
        fill="#4caf50",
    )

    # Arrow triangle: points 26,26 38,32 26,38
    draw.polygon(
        [(int(26 * s), int(26 * s)), (int(38 * s), int(32 * s)), (int(26 * s), int(38 * s))],
        fill="#4caf50",
    )

    return img


if __name__ == "__main__":
    sizes = [16, 32, 48, 256]
    images = [draw_icon(s) for s in sizes]

    # Save as ICO with multiple sizes
    images[-1].save(
        "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print("Generated icon.ico")
