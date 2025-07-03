
from gameengine import GameEnv
from smartagent import SmartAgent
from state_encoder import encode_state
import torch

# Hyperparameters
num_episodes = 1000
save_every = 50

# Initialize environment and agent
env = GameEnv()
agent = SmartAgent()

for episode in range(num_episodes):
	state = env.reset()
	done = False
	total_reward = 0

	while not done:
		encoded_state = encode_state(state)              # Tensor representation
		action = agent.select_action(encoded_state)      # Get action from model
		next_state, reward, done, info = env.step(action)

		agent.remember(encoded_state, action, reward)    # Store experience
		state = next_state
		total_reward += reward

	agent.learn()                                        # Update model using stored experiences

	print(f"Episode {episode} — Total Reward: {total_reward}")

	if episode % save_every == 0:
		agent.save(f"models/model_ep{episode}.pth")
