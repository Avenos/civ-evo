
import os
import torch
from engine import EnvWrapper  # ✅ only import the class you need
from smart_agent import SmartAgent
from model import Model
from state_encoder import encode_game_state

def train_agent(num_episodes=1000):
	# === Hyperparameters ===
	save_every = 50
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	
	# === Prepare model and agent ===
	model = Model().to(device)
	agent = SmartAgent(model=model, device=device)
	
	# === Prepare environment ===
	env = EnvWrapper()
	engine = env.engine  # ✅ assign game engine instance for easy access
	
	# === Create model directory if it doesn't exist ===
	os.makedirs("models", exist_ok=True)
	
	# === Training Loop ===
	for episode in range(num_episodes):
		state = env.reset()
		done = False
		total_reward = 0
	
		print(f"[DEBUG] Starting Episode {episode + 1}")  # <-- Start of episode
	
		while not done:
			encoded_state = encode_game_state(state).to(device)
	
			# ✅ Get legal actions and select one
			legal_actions = engine.get_legal_actions(engine.current_player)
			action = agent.select_best_action_from(legal_actions, engine)
	
			print(f"[DEBUG] Selected action: {action}")  # <-- Action selection
	
			# ✅ Take action in environment
			next_state, reward, done, info = env.step(action)
	
			# ✅ Remember experience
			agent.remember(encoded_state, action, reward, next_state, done)
	
			state = next_state
			total_reward += reward
	
			print(f"[DEBUG] Step reward: {reward}, Total reward: {total_reward}")  # <-- Step info
	
		# ✅ Learn from episode
		agent.learn()
	
		print(f"Episode {episode + 1}/{num_episodes} — Total Reward: {total_reward}")
	
		# ✅ Save model checkpoint
		if (episode + 1) % save_every == 0:
			print(f"[DEBUG] Saving model at episode {episode + 1}")
			torch.save(model.state_dict(), f"models/model_ep{episode + 1}.pth")
