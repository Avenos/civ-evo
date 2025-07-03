
import torch
from state_encoder import encode_game_state  # assuming you have this
from action_handler import handle_action  # whatever handles game actions

ACTION_TYPES = [
        "move_unit", "found_city", "choose_project", "set_research",
    "purchase_unit", "purchase_building", "purchase_tile",
    "choose_pantheon", "choose_policy", "choose_worked_tiles",
    "assign_tile", "unassign_tile", "end_turn"
]

MAX_ID = 1000
MAX_COORD = 20

def encode_action(action):
	vec = []
	type_vec = [0.0] * len(ACTION_TYPES)
	type_idx = ACTION_TYPES.index(action["action"]) if action["action"] in ACTION_TYPES else 0
	type_vec[type_idx] = 1.0
	vec.extend(type_vec)

	data = action.get("data", {})
	tile_q, tile_r = -1, -1
	if "to" in data:
		tile_q, tile_r = data["to"]
	elif "tile_coords" in data:
		tile_q, tile_r = data["tile_coords"]
	elif "tile" in data:
		tile_q, tile_r = data["tile"]

	vec.append(tile_q / MAX_COORD)
	vec.append(tile_r / MAX_COORD)

	unit_id = data.get("unit_id", -1)
	city_id = data.get("city_id", -1)
	vec.append(unit_id / MAX_ID)
	vec.append(city_id / MAX_ID)

	for key in ["project_name", "policy_name", "tech_name", "pantheon"]:
		name = data.get(key, "")
		name_idx = hash(name) % 1000
		vec.append(name_idx / 1000.0)

	return torch.tensor(vec, dtype=torch.float32)

class SmartAgent:
	def __init__(self, model, device='cpu'):
		self.model = model.to(device)
		self.device = device

	def select_action(self, engine):
		state = engine.get_state()
		input_tensor = encode_game_state(state).to(self.device)
		legal_actions = engine.get_legal_actions(engine.current_player)

		if not legal_actions:
			return None

		best_action = None
		best_score = float("-inf")

		for action in legal_actions:
			action_tensor = encode_action(action).to(self.device)
			full_input = torch.cat([input_tensor, action_tensor], dim=0).unsqueeze(0)

			with torch.no_grad():
				score = self.model(full_input).item()

			if score > best_score:
				best_score = score
				best_action = action

		return best_action

	def run_agent(self, engine, headless=True):
		while engine.turn < 40:
			print(f"Turn {engine.turn} starting")
			while True:
				legal_actions = engine.get_legal_actions(engine.current_player)
				if not legal_actions:
					print("No legal actions left, forcing end_turn")
					handle_action(engine, "end_turn", {}, log_actions=False)
					break
	
				print(f"Legal actions available ({len(legal_actions)}): {[action['action'] for action in legal_actions]}")
	
				best_action = self.select_best_action_from(legal_actions, engine)
				if best_action["action"] == "end_turn":
					handle_action(engine, "end_turn", {}, log_actions=False)
					print("End turn chosen")
					break
	
				success, err = handle_action(engine, best_action["action"], best_action["data"], log_actions=False)
				if success:
					print(f"Executed action: {best_action}")
				else:
					print(f"Failed to execute action: {best_action}, reason: {err}")
	
			# Fitness after turn ends
			total_population = sum(city.population for city in engine.current_player.cities)
			total_science = getattr(engine.current_player, "total_science", 0)
			fitness = total_population + total_science
			print(f"Turn {engine.turn} ended. Fitness: {fitness}")
	
		print("Reached turn 80, stopping.")
	
	def select_best_action_from(self, legal_actions, engine):
		state = engine.get_state()
		input_tensor = encode_game_state(state).to(self.device)
	
		best_action = None
		best_score = float("-inf")
	
		for action in legal_actions:
			action_tensor = encode_action(action).to(self.device)
			full_input = torch.cat([input_tensor, action_tensor], dim=0).unsqueeze(0)
	
			with torch.no_grad():
				score = self.model(full_input).item()
	
			if score > best_score:
				best_score = score
				best_action = action
	
		return best_action
