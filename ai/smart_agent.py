
import torch
import torch.nn as nn
import torch.optim as optim
import random

from .model import Model
from .state_encoder import StateEncoder
from engine import Engine, action_handler

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
	def __init__(self, model, device, lr=1e-4, gamma=0.99):
		self.model = model
		self.device = device
		self.memory = []
		self.optimizer = optim.Adam(model.parameters(), lr=lr)
		self.gamma = gamma
		self.loss_fn = nn.MSELoss()
		self.batch_size = 32
		self.max_memory = 10000

	def remember(self, state, action, reward, next_state, done):
		self.memory.append((state, action, reward, next_state, done))
		if len(self.memory) > self.max_memory:
			self.memory.pop(0)

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
		model = MyModelClass().to(device)

		try:
			model.load_state_dict(torch.load("model.pth", map_location=device))
			model.eval()
			print("[INFO] Loaded trained model from model.pth")
		except FileNotFoundError:
			print("[WARN] model.pth not found. Running with untrained model.")

		engine = build_engine()
		self.model = model
		self.device = device

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

			total_population = sum(city.population for city in engine.current_player.cities)
			total_science = getattr(engine.current_player, "total_science", 0)
			fitness = total_population + total_science
			print(f"Turn {engine.turn} ended. Fitness: {fitness}")

		print("Reached turn 40, stopping.")

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
