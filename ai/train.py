
#here is train.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import os
import torch
from engine import EnvWrapper
from . import SmartAgent, Model, StateEncoder

class Train:
	def __init__(self, num_episodes=1000, save_every=50):
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

			print(f"[DEBUG] Starting Episode {episode + 1}")

			while not done:
				encoded_state = self.state_encoder.encode_game_state(state).to(self.device)

				legal_actions = self.engine.get_legal_actions(self.engine.current_player)
				action = self.agent.select_best_action_from(legal_actions, self.engine)

				print(f"[DEBUG] Selected action: {action}")

				next_state, reward, done, info = self.env.step(action)

				self.agent.remember(encoded_state, action, reward, next_state, done)

				state = next_state
				total_reward += reward

				print(f"[DEBUG] Step reward: {reward}, Total reward: {total_reward}")

			self.agent.learn()

			print(f"Episode {episode + 1}/{self.num_episodes} — Total Reward: {total_reward}")

			if (episode + 1) % self.save_every == 0:
				print(f"[DEBUG] Saving model at episode {episode + 1}")
				torch.save(self.model.state_dict(), f"models/model_ep{episode + 1}.pth")
