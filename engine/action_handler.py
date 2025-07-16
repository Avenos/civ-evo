
#here is action_handler.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import json
import os
from utils import helper, BoolResult
from datetime import datetime
from data import constants

def handle_action(engine, action_type, data, log_actions=False):
	"""
	Game Engine API
	Handles a single action applied to the engine.
	Returns (success: bool, error_msg: str or None)
	"""
	result = BoolResult(False, "Unknown action type")

	if action_type == "move_unit":
		unit = engine.get_unit_by_id(data["unit_id"])
		to_q, to_r = data["to"]
		
		if not unit:
			result = BoolResult(False, "Unit not found")
		else:
			from_tile = engine.tiles[unit.q][unit.r]
			to_tile = engine.tiles[to_q][to_r]
			result = unit.move_to(from_tile, to_tile)

	elif action_type == "found_city":
		unit = engine.get_unit_by_id(data["unit_id"])
		result = engine.current_player.found_city(unit, engine)

	elif action_type == "improve_tile":
		q, r = data["tile_coords"]
		unit = engine.get_unit_by_id(data["unit_id"])
		tile = engine.get_tile(q, r)

		if not unit:
			result = BoolResult(False, "Unit not found.")
			
		result = unit.improve_tile(tile, data["improvement"])

	elif action_type in ["assign_tile", "unassign_tile"]:
		city_id = data.get("city_id")
		q, r = data.get("tile")
	
		city = engine.get_city_by_id(city_id)
		if not city:
			result = BoolResult(False, "City not found")

		elif q is None or r is None:
			return BoolResult(False, "Invalid tile coordinates")		
		
		else:
			tile = engine.tiles[q][r]
			if action_type == "assign_tile":
				result = city.assign_tile(tile, engine)
			else:
				result = city.unassign_tile(tile)

	elif action_type == "choose_project":
		city = engine.get_city_by_id(data["city_id"])
		if not city:
			result = BoolResult(False, "City not found for production choice")
		else:
			result = city.production_system.choose_project(data["project_name"])

	elif action_type == "choose_research":
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
			return BoolResult(False, "Invalid tile coordinates")

		tile = engine.get_tile(q, r)

		result = city.purchase_tile(tile, engine) if city else BoolResult(False, "City not found")

	elif action_type == "choose_pantheon":
		pantheon_name = data.get("pantheon_name")
		result = engine.current_player.choose_pantheon(pantheon_name)

	elif action_type == "choose_policy":
		policy = data.get("policy_name")
		result = engine.current_player.choose_policy(policy, engine)

	elif action_type == "establish_trade_route":
		unit = engine.get_unit_by_id(data["unit_id"])
		dest_city = engine.get_city_by_id(data["dest_city_id"])
		if not unit:
			result = BoolResult(False, "Unit not found.")
		elif not dest_city:
			result = BoolResult(False, "Destination city not found.")
		else:
			result = unit.establish_trade_route(dest_city, engine)
	
	elif action_type == "rebase_caravan":
		unit = engine.get_unit_by_id(data["unit_id"])
		dest_city = engine.get_city_by_id(data["dest_city_id"])
		if not unit:
			result = BoolResult(False, "Unit not found.")
		elif not dest_city:
			result = BoolResult(False, "City not found.")
		else:
			result = unit.rebase_to(dest_city)

	elif action_type == "end_turn":
		result = engine.current_player.end_turn(engine)
		print(f"Turn: {engine.turn}")

	if log_actions and result:
		replay_path = getattr(engine, "replay_log_filepath", None)
		if replay_path:
			log_action(engine.turn, action_type, data, replay_path)

	action_summary = {
		"type": action_type,
		"data": data
	}

	status = "VALID" if result else f"INVALID ({result.message})"
	print(f"ACTION: {json.dumps(action_summary, separators=(',', ':'))} --> {status}")

	#legal_actions = engine.get_legal_actions(engine.current_player)
	#print("Legal actions:")
	#for action in legal_actions:
		#print(f" - {action['action']} | { {k: v for k, v in action.items() if k != 'action'} }")

	print("\n")
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
