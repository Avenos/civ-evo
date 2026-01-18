import os
import pygame
import torch

from engine import Engine, HumanGame, Replay, start_new_log
from ai import CivEnv, SmartAgent, Model, train_ppo, EnvConfig

MODE = "train"         # "ai" | "train" | "human" | "replay"
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
		# No pygame loop needed; keep it fast.
		os.makedirs("checkpoints", exist_ok=True)

		train_ppo()
		return

	if MODE == "ai":
		engine = Engine()

		# record a replay of this run
		start_new_log(engine, prefix="replayai", folder="replays")

		model = Model().to(device)

		# load checkpoint if present
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
