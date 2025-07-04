
import pygame
import game_loop
import replay
import torch
import train
from engine import Engine
from model import Model
from smart_agent import SmartAgent

def main():
	pygame.init()
	engine = Engine()
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	# === Uncomment ONE of these at a time ===

	# 1. Train the agent
	#train.train_agent(num_episodes=1000)

	# 2. Run smart agent using trained model
	# model = MyModelClass().to(device)
	# try:
	#     model.load_state_dict(torch.load("model.pth", map_location=device))
	#     model.eval()
	#     print("[INFO] Loaded trained model from model.pth")
	# except FileNotFoundError:
	#     print("[WARN] model.pth not found. Running with untrained model.")
	# agent = SmartAgent(model, device=device)
	# agent.run_agent(engine, headless=False)

	# 3. Manual human-controlled game
	game_loop.run_manual_game(engine)

	# 4. Replay from saved game file
	# replay.play_replay("replay_2025-06-22_21-36-40.json", engine, speed=1.0)

if __name__ == "__main__":
	main()
