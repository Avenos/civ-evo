#possible actions: (also replicate in all legal actions in engine)
#move a unit to a tile DONE
#start production in a city DONE
#purchase a tile or unit or building DONE
#settle a city DONE
#choose a tech DONE, limit to once per turn?
#choose social policy DONE
#choose a pantheon DONE
#choose tiles worked by cities
#assign a trade route
#sell a building eh...

import json
import os
from datetime import datetime
from data import constants

def handle_action(engine, action_type, data, log_actions=True):
	"""
	Game Engine API
	Handles a single action applied to the engine.
	Returns (success: bool, error_msg: str or None)
	"""
	result = (False, "Unknown action type")

	if action_type == "move_unit":
		unit = engine.get_unit_by_id(data["unit_id"])
		to_q, to_r = data["to"]
		if not unit:
			result = (False, "Unit not found")
		else:
			from_tile = engine.tiles[unit.q][unit.r]
			to_tile = engine.tiles[to_q][to_r]
			result = unit.move_to(from_tile, to_tile)

	elif action_type == "found_city":
		unit = engine.get_unit_by_id(data["unit_id"])
		if not unit:
			result = (False, "Unit not found for founding city")
		else:
			result = engine.current_player.found_city(unit, engine)

	elif action_type == "choose_worked_tiles":
		city_id = data.get("city_id")
		tile_coords = data.get("tiles")  # list of (q, r) tuples

		city = engine.get_city_by_id(city_id)
		if not city:
			result = (False, "City not found")
		else:
			# Convert coords to tile objects
			tiles = []
			for q, r in tile_coords:
				if q < 0 or r < 0 or q >= len(engine.tiles) or r >= len(engine.tiles[0]):
					result = (False, f"Tile coords ({q},{r}) out of bounds")
					break
				tiles.append(engine.tiles[q][r])
			else:
				result = city.set_worked_tiles(tiles, engine)

	elif action_type == "assign_tile":
		city_id = data.get("city_id")
		q, r = data.get("tile")
		city = engine.get_city_by_id(city_id)
		if not city:
			result = (False, "City not found")
		elif q < 0 or r < 0 or q >= len(engine.tiles) or r >= len(engine.tiles[0]):
			result = (False, f"Tile coords ({q},{r}) out of bounds")
		else:
			tile = engine.tiles[q][r]
			result = city.assign_tile(tile, engine)

	elif action_type == "unassign_tile":
		city_id = data.get("city_id")
		q, r = data.get("tile")
		city = engine.get_city_by_id(city_id)
		if not city:
			result = (False, "City not found")
		elif q < 0 or r < 0 or q >= len(engine.tiles) or r >= len(engine.tiles[0]):
			result = (False, f"Tile coords ({q},{r}) out of bounds")
		else:
			tile = engine.tiles[q][r]
			result = city.unassign_tile(tile)    

	elif action_type == "choose_project":
		city = engine.get_city_by_id(data["city_id"])
		if not city:
			result = (False, "City not found for production choice")
		else:
			result = city.production_system.choose_project(data["project_name"])

	elif action_type == "set_research":
		result = engine.current_player.science_system.set_current_research(data["tech_name"]) 

	elif action_type == "purchase_unit":
		city = engine.get_city_by_id(data["city_id"])
		result = city.purchase_unit(data["name"], engine.current_player) if city else (False, "City not found")

	elif action_type == "purchase_building":
		city = engine.get_city_by_id(data["city_id"])
		result = city.purchase_building(data["name"], engine.current_player) if city else (False, "City not found")

	elif action_type == "purchase_tile":
		city = engine.get_city_by_id(data["city_id"])
		q, r = data.get("tile_coords", (None, None))
		if q is None or r is None:
			return False, "Invalid tile coordinates"
		if 0 <= q < GRID_WIDTH and 0 <= r < GRID_HEIGHT:
			tile = engine.tiles[q][r]
		else:
			return False, "Tile coordinates out of bounds"
		result = city.purchase_tile(tile, engine) if city else (False, "City not found")

	elif action_type == "choose_pantheon":
		pantheon_name = data.get("pantheon_name")
		result = engine.current_player.choose_pantheon(pantheon_name)

	elif action_type == "choose_policy":
		policy = data.get("policy_name")
		result = engine.current_player.choose_policy(policy, engine)

	elif action_type == "end_turn":
		result = engine.current_player.end_turn(engine)
		print(f"Turn: {engine.turn}")

	if log_actions and result[0]:
		replay_path = getattr(engine, "replay_log_filepath", None)
		if replay_path:
			log_action(engine.turn, action_type, data, replay_path)

	action_summary = {
		"type": action_type,
		"data": data
	}

	status = "VALID" if result[0] else f"INVALID ({result[1]})"
	#print(f"ACTION: {json.dumps(action_summary, separators=(',', ':'))} --> {status}")

	#legal_actions = engine.get_legal_actions(engine.current_player)
	#print("Legal actions:")
	#for action in legal_actions:
		#print(f" - {action['action']} | { {k: v for k, v in action.items() if k != 'action'} }")

	#print("\n")
	return result

def start_new_log(engine, prefix="replay", folder="replays"):
	os.makedirs(folder, exist_ok=True)
	timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
	filename = f"{prefix}_{timestamp}.json"
	filepath = os.path.join(folder, filename)
	engine.replay_log_filepath = filepath

	with open(filepath, "w") as f:
		json.dump([], f)

def log_action(turn, action_type, data, filepath="replays/replay.json"):
	os.makedirs("replays", exist_ok=True)

	if os.path.exists(filepath):
		with open(filepath, "r") as f:
			try:
				log = json.load(f)
			except json.JSONDecodeError:
				log = []
	else:
		log = []

	action = [turn, action_type, data]
	log.append(action)

	with open(filepath, "w") as f:
		f.write("[\n")
		for i, entry in enumerate(log):
			line = json.dumps(entry, separators=(',', ':'))
			if i < len(log) - 1:
				f.write(f"  {line},\n")
			else:
				f.write(f"  {line}\n")
		f.write("]\n")
