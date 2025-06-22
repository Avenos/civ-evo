
import dictionary
import pygame
import constants
import math
import os
import helper
from collections import deque
import heapq
import pygame
import os
import helper
from constants import WIDTH, HEIGHT, GRID_WIDTH, GRID_HEIGHT

def init_pygame_assets():
	pygame.display.init()
	pygame.font.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))  # adjust size as needed
	pygame.display.set_caption("Civ V Build Order Optimizer Replay")
	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 20)
	big_font = pygame.font.SysFont(None, 24)

	terrain_overlays = {}
	for filename in os.listdir("assets"):
		if filename.endswith(".png"):
			key = filename[:-4]
			image = pygame.image.load(os.path.join("assets", filename)).convert_alpha()
			terrain_overlays[key] = image

	yield_types = ["food", "production", "gold", "science", "culture", "faith", "happiness", "unhappiness"]
	icon_images = {}
	for yield_type in yield_types:
		icon_images[yield_type] = pygame.image.load(f"assets/icons/{yield_type}.png").convert_alpha()

	unit_icons = helper.load_unit_icons()

	return screen, clock, font, big_font, terrain_overlays, icon_images, unit_icons


def a_star_path(start, goal, game_map, move_points_per_turn=2):
	"""
	Finds the fastest path (in turns) from start to goal.

	Args:
	    start (tuple): (q, r)
	    goal (tuple): (q, r)
	    game_map (dict): {(q, r): Tile}
	    move_points_per_turn (int): Unit's movement points per turn

	Returns:
	    List of (q, r) tiles from start to goal, in order
	"""

	def reconstruct_path_grouped(came_from, current_state):
		"""
		Returns a list of turns, where each turn is a list of (from → to) steps.
		"""
		path = []
		while current_state in came_from:
			prev_state = came_from[current_state]
			path.append((prev_state, current_state))
			current_state = prev_state
		path.reverse()

		grouped = []
		current_turn = -1
		turn_moves = []
		for prev, curr in path:
			_, curr_turn, _ = curr
			pos_from = prev[0]
			pos_to = curr[0]
			if curr_turn != current_turn:
				if turn_moves:
					grouped.append(turn_moves)
				turn_moves = [(pos_from, pos_to)]
				current_turn = curr_turn
			else:
				turn_moves.append((pos_from, pos_to))

		if turn_moves:
			grouped.append(turn_moves)

		return grouped

	def heuristic(a, b):
		return hex_distance(a[0], a[1], b[0], b[1])

	open_set = []
	start_state = (start, 0, move_points_per_turn)  # (pos, turns_used, mp_remaining)
	heapq.heappush(open_set, (heuristic(start, goal), start_state))

	came_from = {}
	cost_so_far = {start_state: 0}

	while open_set:
		_, current = heapq.heappop(open_set)
		current_pos, turns_used, mp_remaining = current

		if current_pos == goal:
			grouped_path = reconstruct_path_grouped(came_from, current)
			print(f"Reached goal {goal} in {len(grouped_path)} turns.")
			for i, moves in enumerate(grouped_path, 1):
				move_str = " → ".join(f"{step[0]}" for step in moves) + f" → {moves[-1][1]}"
				print(f"Turn {i}: {move_str}")

			remaining_mp = current[2]
			if remaining_mp > 0:
				print(f"Arrived at goal with {remaining_mp} movement points left.")
			else:
				print("Arrived at goal with no movement remaining.")
			return [step[0] for moves in grouped_path for step in moves] + [goal]

		for neighbor in hex_neighbors(*current_pos):
			if neighbor not in game_map:
				continue

			current_tile = game_map[current_pos]
			neighbor_tile = game_map[neighbor]

			if not getattr(neighbor_tile, "passable", True):
				continue

			crossing_river = helper.has_river_between(current_tile, neighbor_tile)
			cost_to_enter = neighbor_tile.movement_cost

			# Movement logic
			if mp_remaining <= 0:
				new_turns = turns_used + 1
				new_mp = move_points_per_turn - cost_to_enter
			else:
				new_turns = turns_used
				new_mp = mp_remaining - cost_to_enter

			if crossing_river:
				new_mp = 0

			new_state = (neighbor, new_turns, new_mp)
			new_cost = new_turns

			if new_state not in cost_so_far or new_cost < cost_so_far[new_state]:
				cost_so_far[new_state] = new_cost
				priority = new_cost + heuristic(neighbor, goal) / move_points_per_turn
				heapq.heappush(open_set, (priority, new_state))
				came_from[new_state] = current

	print("No path found.")
	return None

def hex_to_pixel(q, r):
	x = constants.HEX_RADIUS * math.sqrt(3) * (q + 0.5 * (r & 1))
	y = constants.HEX_RADIUS * 3/2 * r
	return (x + 50, y + 50)

def oddr_to_cube(q, r):
	x = q - (r - (r & 1)) // 2
	z = r
	y = -x - z
	return (x, y, z)

def cube_distance(a, b):
	return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))

def hex_distance(q1, r1, q2, r2):
	c1 = oddr_to_cube(q1, r1)
	c2 = oddr_to_cube(q2, r2)
	return cube_distance(c1, c2)

def hex_neighbors(q, r):
	if r % 2 == 0:
		directions = [(+1, 0), (0, -1), (-1, -1),
			      (-1, 0), (-1, +1), (0, +1)]
	else:
		directions = [(+1, 0), (+1, -1), (0, -1),
			      (-1, 0), (0, +1), (+1, +1)]
	return [(q + dq, r + dr) for dq, dr in directions]

def get_hex_at_pixel(x, y):
	for q in range(constants.GRID_WIDTH):
		for r in range(constants.GRID_HEIGHT):
			hx, hy = hex_to_pixel(q, r)
			if math.hypot(x - hx, y - hy) < constants.HEX_RADIUS:
				return (q, r)
	return None

def get_hex_corner(x, y, i):
	angle_deg = 60 * i - 30  # Pointy-top hexes
	angle_rad = math.radians(angle_deg)
	return (x + constants.HEX_RADIUS * math.cos(angle_rad),
		y + constants.HEX_RADIUS * math.sin(angle_rad))

def create_hex_mask(radius, inset=0):  # inset controls how much border to leave
	adjusted_radius = radius - inset
	mask_surf = pygame.Surface((constants.HEX_DIAMETER, constants.HEX_DIAMETER), pygame.SRCALPHA)
	center = (radius, radius)

	points = []
	for i in range(6):
		angle_deg = 60 * i - 30
		angle_rad = math.radians(angle_deg)
		x = center[0] + adjusted_radius * math.cos(angle_rad)
		y = center[1] + adjusted_radius * math.sin(angle_rad)
		points.append((x, y))

	pygame.draw.polygon(mask_surf, (255, 255, 255, 255), points)
	return mask_surf

def has_river_between(tile1, tile2):
	# First, compute the direction from tile1 to tile2
	dq = tile2.q - tile1.q
	dr = tile2.r - tile1.r

	# Determine if we're in an even or odd row to get the right neighbor offsets
	is_even = (tile1.r % 2 == 0)
	neighbor_offsets = dictionary.EVEN_ROW_NEIGHBORS if is_even else dictionary.ODD_ROW_NEIGHBORS

	# Find the direction that matches the offset
	direction = None
	for dir_name, (offset_q, offset_r) in neighbor_offsets.items():
		if (dq, dr) == (offset_q, offset_r):
			direction = dir_name
			break

	if direction is None:
		raise ValueError("Tiles are not neighbors")

	# Get edge index for tile1 and opposite edge index for tile2
	edge1 = dictionary.DIRECTION_TO_EDGE[direction]
	opposite_direction = dictionary.OPPOSITE_DIRECTION[direction]
	edge2 = dictionary.DIRECTION_TO_EDGE[opposite_direction]

	return edge1 in tile1.rivers or edge2 in tile2.rivers

def add_river(tile, edge_index, tiles_map):
	tile.rivers.add(edge_index)

	for direction, idx in dictionary.DIRECTION_TO_EDGE.items():
		if idx == edge_index:
			break
	else:
		raise ValueError(f"Invalid edge index: {edge_index}")

	# Get offset for that direction depending on row parity
	offsets = dictionary.EVEN_ROW_NEIGHBORS if tile.r % 2 == 0 else dictionary.ODD_ROW_NEIGHBORS
	dq, dr = offsets[direction]

	neighbor_q = tile.q + dq
	neighbor_r = tile.r + dr

	try:
		neighbor = tiles_map[neighbor_q][neighbor_r]
		opposite_edge = dictionary.DIRECTION_TO_EDGE[dictionary.OPPOSITE_DIRECTION[direction]]
		neighbor.rivers.add(opposite_edge)
	except (IndexError, KeyError):
		# Neighbor is off-map
		pass

def is_adjacent_to_owned_tile(tile, player, engine):
	q, r = tile.q, tile.r
	neighbors = []

	print(f"Checking adjacency for tile ({q}, {r})")

	if r % 2 == 0:
		offsets = dictionary.EVEN_ROW_NEIGHBORS.values()
	else:
		offsets = dictionary.ODD_ROW_NEIGHBORS.values()

	for dq, dr in offsets:
		nq, nr = q + dq, r + dr
		if 0 <= nq < GRID_WIDTH and 0 <= nr < GRID_HEIGHT:
			neighbors.append((nq, nr))

	print("Neighbors:", neighbors)

	for nq, nr in neighbors:
		neighbor_tile = engine.tiles[nq][nr]
		owner = neighbor_tile.owner
		print(f"Neighbor ({nq}, {nr}) owned by:", owner)
		if owner == player:
			print("Adjacent tile found!")
			return True

	print("No adjacent owned tiles found.")
	return False

def spawn_unit_near_capital(player, game, name, message):
	if not player.cities:
		game.show_message(f"No cities to place free {name}!", 120)
		return False

	capital = player.cities[0]
	q, r = capital.q, capital.r

	for dir_idx in range(6):
		dq, dr = hex_direction(dir_idx)  # make sure this helper exists in helper.py
		nq, nr = q + dq, r + dr

		if 0 <= nq < game.GRID_WIDTH and 0 <= nr < game.GRID_HEIGHT:
			tile = game.tiles[nq][nr]
			if tile.unit is None and tile.city is None:
				game.spawn_unit(player, q, r, name)
				game.show_message(message, 120)
				return True

	game.show_message(f"No space near capital to place {name}!", 120)
	return False

def build_policy_objects(policy_dict):
	from systems import Policy
	return {name: Policy(name, **details) for name, details in policy_dict.items()}

def build_tech_objects(tech_dict):
	from systems import Tech

	tech_list = []
	for name, data in tech_dict.items():
		tech = Tech(
			name=name,
			base_cost=data["base_cost"],
			prerequisites=data.get("prerequisites", [])
		)
		tech.progress = data.get("progress", 0)
		tech.unlocked = data.get("unlocked", False)
		tech_list.append(tech)
	return tech_list

def build_building_object(building_name, building_data):
	from core import Building
	return Building(
		name=building_name,
		food=building_data.get("food", 0),
		production=building_data.get("production", 0),
		gold=building_data.get("gold", 0),
		science=building_data.get("science", 0),
		culture=building_data.get("culture", 0),
		happiness=building_data.get("happiness", 0),
		growth_percentage=building_data.get("growth_percentage", 0),
		science_percentage=building_data.get("science_percentage", 0),
		production_percentage=building_data.get("production_percentage", 0),
		gold_percentage=building_data.get("gold_percentage", 0),

		production_cost=building_data.get("production_cost", 0),
		gold_cost=building_data.get("gold_cost", 0),
		techs_required=building_data.get("techs_required", []),
		policies_required=building_data.get("policies_required", []),
		buildings_required=building_data.get("buildings_required", []),
	)

def build_unit_object(name, data):
	from core import Unit
	return Unit(
		name=name,
		player=None,  # Assign player later...
		q=None,       # Assign position later...
		r=None,
		hp=data.get("hp", 100),
		moves=data.get("moves", 2),
		gold_cost=data.get("gold_cost", 0),
		production_cost=data.get("production_cost", 0),
		techs_required=data.get("techs_required", []),
		policies_required=data.get("policies_required", [])
	)

#is this expensive?
def check_proximity_rewards(game, player):
	for tile_coords in game.special_tiles:
		q, r = tile_coords

		# Initialize reward tracking if missing
		if tile_coords not in game.tile_rewards_claimed:
			game.tile_rewards_claimed[tile_coords] = set()

		# Skip if player already claimed reward for this tile
		if player.name in game.tile_rewards_claimed[tile_coords]:
			continue

		# Check if any of the player's units are within range
		for unit in player.units:
			dist = helper.hex_distance(unit.q, unit.r, q, r)  # ✅ correct
			if dist <= 3:
				player.gold += 30
				player.faith += 8
				game.show_message(f"{player.name} discovered a city-state! +30 gold, +8 faith", 120)

				game.tile_rewards_claimed[tile_coords].add(player.name)
				break  # Only reward once per tile per player

def build_tile_image_key(tile, available_images):
	terrain_key = tile.terrain_type.lower()
	terrain = dictionary.TERRAIN_TYPES.get(terrain_key, {}).get("name", "grassland").lower()
	elev = tile.elevation
	trees = tile.trees

	if terrain_key == 'n' and elev == 2:
		if "mountain" in available_images:
			return "mountain"

	if terrain_key == 'l':
		if "coast" in available_images:
			return "coast"

	candidates = [
		f"{terrain}_hill_jungle" if elev == 1 and trees == 2 else None,
		f"{terrain}_hill_forest" if elev == 1 and trees == 1 else None,
		f"{terrain}_hill" if elev == 1 else None,
		f"{terrain}_jungle" if trees == 2 else None,
		f"{terrain}_forest" if trees == 1 else None,
		terrain
	]

	for key in candidates:
		if key and key in available_images:
			return key

	return None

def load_unit_icons(path="assets/units"):
	icons = {}
	for filename in os.listdir(path):
		if filename.lower().endswith(".png"):
			unit_name = os.path.splitext(filename)[0].lower()  # filename without extension
			full_path = os.path.join(path, filename)
			icon = pygame.image.load(full_path).convert_alpha()
			icons[unit_name] = icon
	return icons

