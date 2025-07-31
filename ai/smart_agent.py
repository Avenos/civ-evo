
#here is smart_agent.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import torch
import torch.nn as nn
import torch.optim as optim
import random

from .model import Model
from .state_encoder import StateEncoder
from engine import Engine, action_handler

ACTION_TYPES = [
	"move_unit", "found_city", "choose_project", "choose_research",
	"purchase_unit", "purchase_building", "purchase_tile",
	"choose_pantheon", "choose_policy", "improve_tile",
	"assign_tile", "unassign_tile", "end_turn" #caravan, 
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
	def __init__(self, model, device, lr=1e-4, gamma=0.99):
		self.model = model
		self.device = device
		self.memory = []
		self.optimizer = optim.Adam(model.parameters(), lr=lr)
		self.gamma = gamma
		self.loss_fn = nn.MSELoss()
		self.batch_size = 32
		self.max_memory = 10000
		self.state_encoder = StateEncoder()

		self.action_type_to_idx = {
			"move_unit": 0,
			"found_city": 1,
			"improve_tile": 2,
			"choose_worked_tiles": 3,
			"assign_tile": 4,
			"unassign_tile": 5,
			"choose_project": 6,
			"choose_research": 7,
			"purchase_unit": 8,
			"purchase_building": 9,
			"purchase_tile": 10,
			"choose_pantheon": 11,
			"choose_policy": 12,
			"end_turn": 13
		}

		# Example vocabularies for categorical data
		self.improvement_to_idx = {"farm": 0, "mine": 1, "road": 2, "lumbermill": 3}
		self.project_to_idx = {"granary": 0, "library": 1}
		self.tech_to_idx = {"pottery": 0, "mining": 1}
		self.pantheon_to_idx = {"fertility": 0, "god_of_war": 1}
		self.policy_to_idx = {"liberty": 0, "tradition": 1}
		self.unit_name_to_idx = {"warrior": 0, "settler": 1}
		self.building_name_to_idx = {"granary": 0, "barracks": 1}

		self.max_worked_tiles = 32  # max tiles for choose_worked_tiles		

	def remember(self, state, action, reward, next_state, done):
		state_tensor = self.state_encoder.encode_game_state(state).to(self.device)
		next_state_tensor = self.state_encoder.encode_game_state(next_state).to(self.device)
		action_tensor = self.encode_action(action)
		self.memory.append((state_tensor, action_tensor, reward, next_state_tensor, done))
		if len(self.memory) > self.max_memory:
			self.memory.pop(0)

	def encode_action(self, action_dict):
		action_name = action_dict.get("action")
		action_idx = self.action_type_to_idx.get(action_name, -1)
		if action_idx == -1:
			raise ValueError(f"Unknown action type: {action_name}")

		# Start encoding: one-hot or integer for action type + parameters
		# For simplicity, put everything in a fixed length tensor

		# We'll create a vector of length N (say 20), pad zeros if unused
		vec = torch.zeros(20, dtype=torch.float32, device=self.device)
		vec[0] = action_idx  # first element = action type index

		data = action_dict.get("data", {})

		try:
			if action_name == "move_unit":
				# encode 'to' coords normalized by map size (assume map size 20x20 here)
				to_q, to_r = data["to"]
				vec[1] = to_q / 20
				vec[2] = to_r / 20

			elif action_name == "found_city":
				# encode unit_id as a normalized int (you can adjust)
				vec[1] = data.get("unit_id", 0) / 1000

			elif action_name == "improve_tile":
				q, r = data["tile_coords"]
				improvement_idx = self.improvement_to_idx.get(data["improvement"], -1)
				vec[1] = q / 20
				vec[2] = r / 20
				vec[3] = improvement_idx if improvement_idx >= 0 else 0

			elif action_name == "choose_worked_tiles":
				tiles = data.get("tiles", [])
				for i in range(min(len(tiles), self.max_worked_tiles)):
					q, r = tiles[i]
					vec[1 + i*2] = q / 20
					vec[2 + i*2] = r / 20
				# pad remaining with zeros

			elif action_name in ["assign_tile", "unassign_tile", "purchase_tile"]:
				q, r = data.get("tile", (0,0))
				vec[1] = q / 20
				vec[2] = r / 20
				# city_id can be encoded as well if needed

			elif action_name == "choose_project":
				project_idx = self.project_to_idx.get(data.get("project_name", ""), 0)
				vec[1] = project_idx

			elif action_name == "choose_research":
				tech_idx = self.tech_to_idx.get(data.get("tech_name", ""), 0)
				vec[1] = tech_idx

			elif action_name == "purchase_unit":
				unit_idx = self.unit_name_to_idx.get(data.get("name", ""), 0)
				vec[1] = unit_idx

			elif action_name == "purchase_building":
				building_idx = self.building_name_to_idx.get(data.get("name", ""), 0)
				vec[1] = building_idx

			elif action_name == "choose_pantheon":
				pantheon_idx = self.pantheon_to_idx.get(data.get("pantheon_name", ""), 0)
				vec[1] = pantheon_idx

			elif action_name == "choose_policy":
				policy_idx = self.policy_to_idx.get(data.get("policy_name", ""), 0)
				vec[1] = policy_idx

			elif action_name == "end_turn":
				# no params needed
				pass
		except Exception as e:
			print(f"Error encoding action {action_dict}: {e}")

		return vec

	def select_action(self, encoded_state):
		epsilon = 0.1
		if random.random() < epsilon:
			return torch.tensor([random.randint(0, 10)], device=self.device)
		else:
			with torch.no_grad():
				q_value = self.model(encoded_state)
				return q_value.argmax()

	def learn(self):
		if len(self.memory) < self.batch_size:
			return

		batch = random.sample(self.memory, self.batch_size)
		states, actions, rewards, next_states, dones = zip(*batch)

		states = torch.stack(states).to(self.device)
		actions = torch.stack(actions).to(self.device)
		rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
		next_states = torch.stack(next_states).to(self.device)
		dones = torch.tensor(dones, dtype=torch.float32).to(self.device)

		current_q = self.model(states).squeeze()
		with torch.no_grad():
			next_q = self.model(next_states).squeeze()
			target_q = rewards + self.gamma * next_q * (1 - dones)

		loss = self.loss_fn(current_q, target_q)

		self.optimizer.zero_grad()
		loss.backward()
		self.optimizer.step()

	def run_agent(self, headless=True):
		device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
		model = Model().to(device)

		try:
			model.load_state_dict(torch.load("model.pth", map_location=device))
			model.eval()
			print("[INFO] Loaded trained model from model.pth")
		except FileNotFoundError:
			print("[WARN] model.pth not found. Running with untrained model.")

		engine = build_engine()
		self.model = model
		self.device = device

		while engine.turn < 121:
			print(f"Turn {engine.turn} starting")
			while True:
				legal_actions = engine.get_legal_actions(engine.current_player)
				if not legal_actions:
					print("No legal actions left, forcing end_turn")
					handle_action(engine, "end_turn", {})
					break

				print(f"Legal actions available ({len(legal_actions)}): {[action['action'] for action in legal_actions]}")

				best_action = self.select_best_action_from(legal_actions, engine)
				if best_action["action"] == "end_turn":
					handle_action(engine, "end_turn", {})
					print("End turn chosen")
					break

				result = handle_action(engine, best_action["action"], best_action["data"])
				if result:
					print(f"Executed action: {best_action}")
				else:
					print(f"Failed to execute action: {best_action}, reason: {result.message}")

			total_population = sum(city.population for city in engine.current_player.cities)
			total_science = getattr(engine.current_player, "total_science", 0)
			fitness = total_population + total_science
			print(f"Turn {engine.turn} ended. Fitness: {fitness}")

		print("Reached turn 40, stopping.")

	def select_best_action_from(self, legal_actions, engine):
		state = engine.get_state()
		input_tensor = self.state_encoder.encode_game_state(state).to(self.device)

		best_action = None
		best_score = float("-inf")

		for action in legal_actions:
			action_tensor = self.encode_action(action).to(self.device)
			full_input = torch.cat([input_tensor, action_tensor], dim=0).unsqueeze(0)

			with torch.no_grad():
				score = self.model(full_input).item()

			if score > best_score:
				best_score = score
				best_action = action

		return best_action
