
import json
import time
import pygame
import renderer
import helper
import os
from constants import HEX_RADIUS
from collections import defaultdict
from action_handler import handle_action

def play_replay(replay_filename, engine, speed=1.0):
	screen, clock, font, big_font, terrain_overlays, resource_icons, unit_icons = helper.init_pygame_assets()
	replay_path = os.path.join('replays', replay_filename)

	if os.path.isfile(replay_path):
		with open(replay_path, 'r') as f:
			actions = json.load(f)
	else:
		raise FileNotFoundError(f"Replay file not found in 'replays': {replay_filename}")

	actions_by_turn = defaultdict(list)
	for action in actions:
		turn, action_type, data = action
		actions_by_turn[turn].append((action_type, data))

	for turn in sorted(actions_by_turn.keys()):
		for action_type, data in actions_by_turn[turn]:
			handle_action(engine, action_type, data, False)

			screen.fill((255, 255, 255))
			hex_mask = helper.create_hex_mask(HEX_RADIUS)
			renderer.draw_grid(screen, engine, font, big_font, terrain_overlays, hex_mask, resource_icons)
			renderer.draw_territory_shading(screen, engine, font, big_font)
			renderer.draw_cities(screen, engine, font, big_font)
			renderer.draw_units(screen, engine, font, big_font, unit_icons)
			renderer.draw_ui(screen, engine, font, big_font, resource_icons)
			renderer.draw_message(screen, engine)
			pygame.display.flip()

			time.sleep(0.05 / speed)

		success = engine.end_turn() #or call it as an action?

		if not success: #hmmmm
			print(f"Replay error: Could not end turn {turn} — required choices missing")
			break

		time.sleep(1.0 / speed)
