
import json
import random
import dictionary

def generate_random_map(grid_width, grid_height, resource_chance=0.15, tree_chance=0.25):
    terrain_keys = list(dictionary.TERRAIN_TYPES.keys())
    resource_keys = [r for r in dictionary.RESOURCES if r != "n"]

    tiles = []

    for row in range(grid_height):
        tile_row = []
        for col in range(grid_width):
            terrain = random.choice(terrain_keys[:-1])  # avoid "none" tiles randomly
            elevation = 0 if terrain != "n" else 2

            # Tree logic
            if terrain == "p":
                tree = random.choices([0, 1, 2], weights=[1 - tree_chance, tree_chance * 0.6, tree_chance * 0.4])[0]
            elif terrain in ["g", "t"]:
                tree = random.choices([0, 1], weights=[1 - tree_chance, tree_chance])[0]
            else:
                tree = 0

            # Jungle only on plains
            if tree == 2 and terrain != "p":
                tree = 0

            # Resource logic
            resources = []
            if random.random() < resource_chance:
                resource = random.choice(resource_keys)
                resources.append(resource)

            tile_row.append([terrain, elevation, tree, resources])

        tiles.append(tile_row)

    return tiles

def save_map_to_json(tiles, filename, grid_width, grid_heigh):
    with open(filename, "w") as f:
        f.write('[\n')
        for i, row in enumerate(tiles):
            json_row = json.dumps(row)
            if i < len(tiles) - 1:
                f.write(f'  {json_row},\n')
            else:
                f.write(f'  {json_row}\n')
        f.write(']')