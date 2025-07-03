
import pygame
import game_loop
import replay
import torch
from engine import Engine
from my_model import MyModelClass
from smartAgent import SmartAgent

def main():
	pygame.init()

	engine = Engine()

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	model = MyModelClass().to(device)

	# Optional: Force CUDA (uncomment if needed)
	# device = torch.device("cuda")
	# model = MyModelClass().to(device)

	try:
		model.load_state_dict(torch.load("model.pth", map_location=device))
		model.eval()
		print("[INFO] Loaded trained model from model.pth")
	except FileNotFoundError:
		print("[WARN] model.pth not found. Running with untrained model.")

	# === Instantiate Agent and Run ===
	agent = SmartAgent(model, device=device)
	agent.run_agent(engine, headless=False)

	# === Alternatives ===
	# game_loop.run_manual_game(engine)
	# replay.play_replay("replay_2025-06-22_21-36-40.json", engine, speed=1.0)

if __name__ == "__main__":
	main()
