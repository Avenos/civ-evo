import os
import pygame
import torch

from engine import Engine, HumanGame, Replay, start_new_log
from ai import SmartAgent, Model

# --------------------------------------------
# Main mode switch
# --------------------------------------------
MODE = "ai"       # "ai" | "train" | "human" | "replay"
REPLAY_FILE = "replay.json"
REPLAY_SPEED = 1

CKPT_PATH = os.path.join("checkpoints", "model_latest.pt")

MAX_TURNS = 80  # consistent with your objective horizon


def main():
	pygame.init()

	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	# -------------------------
	# REPLAY MODE
	# -------------------------
	if MODE == "replay":
		engine = Engine()
		Replay(REPLAY_FILE, engine, speed=REPLAY_SPEED).run()
		return

	# -------------------------
	# HUMAN MODE
	# -------------------------
	if MODE == "human":
		engine = Engine()
		HumanGame(engine).run()
		return

	# -------------------------
	# TRAIN MODE (headless)
	# -------------------------
	if MODE == "train":
		# No pygame loop needed; keep it fast.
		os.makedirs("checkpoints", exist_ok=True)

		from rl.train_ppo import train_ppo  # imported here to avoid pygame coupling
		from rl.civ_env import EnvConfig

		train_ppo(
	        ckpt_path=CKPT_PATH,
	    env_cfg=EnvConfig(horizon_turns=MAX_TURNS),
	    device=device,
	)
		return

	# -------------------------
	# AI PLAY MODE (pygame)
	# -------------------------
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
