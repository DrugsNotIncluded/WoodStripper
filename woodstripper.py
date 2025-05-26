# This bullshit is partially written by AI, don't judge me, i don't want to remember how PIL and all it's quirks work
# at least algorithm is mine
# I will rewrite it later, trust me..

from PIL import Image
from math import sqrt
import heapq

def get_inner_crop(image, border=1):
    """Crop out the bark border from the top image."""
    w, h = image.size
    return image.crop((border, border, w - border, h - border))

def get_unique_colors(image):
    """Get all unique RGB colors from an image."""
    return list(set(image.getdata()))

def rgb_distance(c1, c2):
    """Calculate Euclidean distance in RGB space."""
    return sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def quantize_image_and_get_palette(image, num_colors):
    """Quantize an image and return the resulting RGB palette."""
    quantized = image.convert("P", palette=Image.ADAPTIVE, colors=num_colors).convert("RGB")
    return list(set(quantized.getdata()))

def assign_unique_color_matches(source_colors, target_palette):
    """Assign each source color to a unique closest target color using greedy matching."""
    pairs = []
    for s in source_colors:
        for t in target_palette:
            dist = rgb_distance(s, t)
            pairs.append((dist, s, t))
    pairs.sort()

    assigned = {}
    used_targets = set()

    for _, s, t in pairs:
        if s not in assigned and t not in used_targets:
            assigned[s] = t
            used_targets.add(t)

    # Final check
    if len(assigned) != len(source_colors):
        raise ValueError("Not enough colors in target palette to uniquely assign to all source colors.")

    return assigned

def apply_mapping(image, color_map):
    """Apply a color mapping to an image."""
    pixels = list(image.getdata())
    new_pixels = [color_map[p] for p in pixels]
    new_image = Image.new("RGB", image.size)
    new_image.putdata(new_pixels)
    return new_image

def interpolate_palette(palette, target_size):
    """
    Expand palette to target_size by inserting midpoint colors
    between similar pairs in a deterministic way.
    """
    expanded = list(palette)

    def midpoint(c1, c2):
        return tuple((a + b) // 2 for a, b in zip(c1, c2))

    while len(expanded) < target_size:
        # Sort by RGB sum (approx brightness)
        expanded.sort(key=lambda c: sum(c))
        new_colors = []
        for i in range(len(expanded) - 1):
            if len(expanded) + len(new_colors) >= target_size:
                break
            c1 = expanded[i]
            c2 = expanded[i + 1]
            mid = midpoint(c1, c2)
            if mid not in expanded and mid not in new_colors:
                new_colors.append(mid)
        if not new_colors:
            raise ValueError("Palette can't be expanded further (all midpoints already exist)")
        expanded.extend(new_colors)
    return expanded


def apply_palette_from_top_to_side(top_path, side_path, output_path, border=1, min_palette_size=128):
    top_image = Image.open(top_path).convert("RGB")
    side_image = Image.open(side_path).convert("RGB")

    top_inner = get_inner_crop(top_image, border)
    top_colors = get_unique_colors(top_inner)
    side_colors = get_unique_colors(side_image)

    print(f"Top (inner) palette: {len(top_colors)} colors")
    print(f"Side palette: {len(side_colors)} colors")

    # Ensure enough colors in top palette
    # if len(top_colors) < len(side_colors):
    #     print("Quantizing top inner region...")
    #     top_colors = quantize_image_and_get_palette(top_inner, max(len(side_colors), min_palette_size))
    #     print(f"New quantized top palette: {len(top_colors)} colors")


    if len(top_colors) < len(side_colors):
        print("Expanding top center palette...")
        top_colors = interpolate_palette(top_colors, len(side_colors))
        print(f"Expanded top palette: {len(top_colors)} colors")

    # Assign unique matches
    color_map = assign_unique_color_matches(side_colors, top_colors)
    print(f"Color mapping established: {len(color_map)} pairs")

    # Recolor and save
    result = apply_mapping(side_image, color_map)
    result.save(output_path)
    print(f"Recolored side saved to: {output_path}")

# Example usage
apply_palette_from_top_to_side("silverwoodtop.png", "silverwoodside.png", "side_log_recolored.png")

# If you have wood with the same texture as minecraft one better just snatch it's stripped variant and apply a color mask, bruh