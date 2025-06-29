
import torch
import torch.nn as nn
import torch.optim as optim
import random

# A dumb simple policy network
class PolicyNet(nn.Module):
	def __init__(self, state_size, action_size):
		super().__init__()
		self.fc = nn.Sequential(
			nn.Linear(state_size, 128),
			nn.ReLU(),
			nn.Linear(128, action_size)
		)

	def forward(self, x):
		return self.fc(x)

# Your "env wrapper"
class CivEnv:
	def reset(self):
		# Reset the game, return initial state
		self.engine = make_new_game()
		return self.get_state()

	def step(self, action_index):
		action = self.legal_actions[action_index]
		result = self.engine.perform_action(action)
		reward = compute_reward(self.engine)
		done = self.engine.is_game_over()
		new_state = self.get_state()
		return new_state, reward, done

	def get_state(self):
		# Flatten game state to a vector (must be numerical)
		return torch.tensor(serialize_game_state(self.engine), dtype=torch.float)

	def get_legal_actions(self):
		self.legal_actions = get_legal_actions(self.engine)
		return self.legal_actions

# Training loop
env = CivEnv()
state_size = 200  # however long your flattened state is
action_size = 50  # max number of legal actions

policy = PolicyNet(state_size, action_size)
optimizer = optim.Adam(policy.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

for episode in range(10000):
	state = env.reset()
	total_reward = 0
	done = False

	while not done:
		legal_actions = env.get_legal_actions()
		logits = policy(state)
		action_probs = torch.softmax(logits[:len(legal_actions)], dim=0)
		action_index = torch.multinomial(action_probs, 1).item()

		new_state, reward, done = env.step(action_index)

		# Simple REINFORCE-style update
		loss = -torch.log(action_probs[action_index]) * reward
		optimizer.zero_grad()
		loss.backward()
		optimizer.step()

		state = new_state
		total_reward += reward

	print(f"Episode {episode} - Total Reward: {total_reward}")
