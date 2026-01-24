import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
import torch

from engine import Engine, HumanGame, Replay, start_new_log
from ai import CivEnv, SmartAgent, Model, train_ppo, EnvConfig

MODE = "human"         # "ai" | "train" | "human" | "replay"
REPLAY_FILE = "replay.json"
REPLAY_SPEED = 1

CKPT_PATH = os.path.join("checkpoints", "model_latest.pt")

MAX_TURNS = 60


def main():
	pygame.init()

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	if MODE == "replay":
		engine = Engine()
		Replay(REPLAY_FILE, engine, speed=REPLAY_SPEED).run()
		return

	if MODE == "human":
		engine = Engine()
		HumanGame(engine).run()
		return

	if MODE == "train":
		os.makedirs("checkpoints", exist_ok=True)

		train_ppo()
		return

	if MODE == "ai":
		engine = Engine()

		start_new_log(engine, prefix="replayai", folder="replays")

		model = Model().to(device)

		if os.path.exists(CKPT_PATH):
			model.load_state_dict(torch.load(CKPT_PATH, map_location=device))
			print(f"[main] loaded checkpoint: {CKPT_PATH}")
		else:
			print("[main] no checkpoint found; using random weights")

		SmartAgent(model, device, deterministic=False).run(engine)
		return

	raise ValueError(f"Unknown MODE={MODE!r}. Use 'ai', 'train', 'human', or 'replay'.")


if __name__ == "__main__":
	main()
