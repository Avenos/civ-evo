
import os
import torch
import random
from engine import EnvWrapper, start_new_log
from . import SmartAgent, Model, StateEncoder

class Train:
	def __init__(self, num_episodes=100, save_every=100):
		self.num_episodes = num_episodes
		self.save_every = save_every
		self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

		# Prepare model and agent
		self.model = Model().to(self.device)
		self.agent = SmartAgent(model=self.model, device=self.device)

		# Prepare environment
		self.env = EnvWrapper()
		self.engine = self.env.engine
		self.state_encoder = StateEncoder()

		# Create model directory
		os.makedirs("models", exist_ok=True)

	def train(self):
		for episode in range(self.num_episodes):
			state = self.env.reset()
			done = False
			total_reward = 0
			turn_counter = 0
	
			# Epsilon for exploration, decay over episodes
			epsilon = max(0.1, 1.0 - episode / (self.num_episodes * 0.8))
	
			print(f"[DEBUG] Starting Episode {episode + 1} with epsilon={epsilon:.2f}")
	
			while not done:
				turn_counter += 1
	
				# Encode current state
				encoded_state = self.state_encoder.encode_game_state(state).to(self.device)
	
				# Get legal actions
				legal_actions = self.engine.get_legal_actions(self.engine.current_player)
	
				# --- Forced exploration for founding city ---
				action = None
				if turn_counter <= 3:
					found_city_actions = [a for a in legal_actions if a["action"] == "found_city"]
					if found_city_actions and random.random() < 0.7:  # 70% chance to force it
						action = found_city_actions[0]
	
				# --- Otherwise epsilon-greedy ---
				if action is None:
					if random.random() < epsilon:
						action = random.choice(legal_actions)
					else:
						action = self.agent.select_best_action_from(legal_actions, self.engine)
	
				# Step environment
				next_state, reward, done, info = self.env.step(action)
				encoded_next_state = self.state_encoder.encode_game_state(next_state).to(self.device)
	
				# --- Ensure exact tensor size ---
				if encoded_state.numel() != 7630:
					pad = torch.zeros(7630 - encoded_state.numel(), device=self.device)
					encoded_state = torch.cat([encoded_state, pad])[:7630]
				if encoded_next_state.numel() != 7630:
					pad = torch.zeros(7630 - encoded_next_state.numel(), device=self.device)
					encoded_next_state = torch.cat([encoded_next_state, pad])[:7630]
	
				# Store experience
				self.agent.remember(encoded_state, action, reward, encoded_next_state, done)
	
				state = next_state
				total_reward += reward
	
			# Learn after episode
			self.agent.learn()
	
			print(f"Episode {episode + 1}/{self.num_episodes} — Total Reward: {total_reward}")
	
			# Save model periodically
			if (episode + 1) % self.save_every == 0:
				print(f"[DEBUG] Saving model at episode {episode + 1}")
				torch.save(self.model.state_dict(), f"models/model_ep{episode + 1}.pth")
