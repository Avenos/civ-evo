
import os
import json
from PIL import Image
import imagehash

class MapParser:
    def __init__(self, map_image_path, template_dir, hex_size):
        self.map_image = Image.open(map_image_path)
        self.template_dir = template_dir
        self.hex_size = hex_size  # (width, height)
        self.templates = self.load_templates()

    def load_templates(self):
        """Load all reference images and associate with a tag like 'plains_forest_flat'."""
        templates = {}
        for filename in os.listdir(self.template_dir):
            if filename.endswith(".png"):
                tag = os.path.splitext(filename)[0]
                img = Image.open(os.path.join(self.template_dir, filename))
                templates[tag] = imagehash.phash(img)
        return templates

    def crop_hex(self, center_x, center_y):
        """Crop a hex area from the map around a given center point."""
        w, h = self.hex_size
        left = center_x - w // 2
        upper = center_y - h // 2
        right = center_x + w // 2
        lower = center_y + h // 2
        return self.map_image.crop((left, upper, right, lower))

    def get_tile_type(self, hex_img):
        """Compare to template hashes and return the best matching terrain tag."""
        tile_hash = imagehash.phash(hex_img)
        best_match = min(self.templates.items(), key=lambda item: tile_hash - item[1])
        return best_match[0]  # e.g., "grassland_hill_forest"

    def parse_map(self, width, height):
        """Process each hex and return structured tile data."""
        tiles = []
        for q in range(width):
            for r in range(height):
                x, y = self.hex_to_pixel(q, r)
                hex_img = self.crop_hex(x, y)
                terrain_tag = self.get_tile_type(hex_img)
                tile = self.parse_tag_to_tile(q, r, terrain_tag)
                tiles.append(tile)
        return tiles

    def parse_tag_to_tile(self, q, r, tag):
        """Turn a terrain tag into structured tile data."""
        terrain, *features = tag.split('_')
        return {
            "q": q,
            "r": r,
            "terrain": terrain,
            "hill": "hill" in features,
            "forest": "forest" in features
        }

    def hex_to_pixel(self, q, r):
        """Convert axial hex coordinates to pixel center."""
        w, h = self.hex_size
        x = w * (3/4 * q)
        y = h * (r + 0.5 * (q % 2))
        return int(x), int(y)

    def export_to_json(self, output_path, tiles):
        with open(output_path, "w") as f:
            json.dump({"tiles": tiles}, f, indent=2)
