
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
	screen, clock, font, big_font, terrain_overlays, icon_images, unit_icons = helper.init_pygame_assets()

	with open(replay_filename, 'r') as f:
		actions = json.load(f)

	# Group actions by turn
	actions_by_turn = defaultdict(list)
	for action in actions:
		turn, action_type, data = action
		actions_by_turn[turn].append((action_type, data))

	# Replay turn by turn
	for turn in sorted(actions_by_turn.keys()):
		for action_type, data in actions_by_turn[turn]:
			handle_action(engine, action_type, data)

			# Render after each action (quickly)
			screen.fill((255, 255, 255))
			hex_mask = helper.create_hex_mask(HEX_RADIUS)
			renderer.draw_grid(screen, engine, font, big_font, terrain_overlays, hex_mask, icon_images)
			renderer.draw_territory_shading(screen, engine, font, big_font)
			renderer.draw_cities(screen, engine, font, big_font)
			renderer.draw_units(screen, engine, font, big_font, unit_icons)
			renderer.draw_ui(screen, engine, font, big_font)
			renderer.draw_message(screen, engine)
			pygame.display.flip()

			# Tiny delay if you want some visual pacing per action (optional)
			time.sleep(0.05 / speed)

		# After all actions for the turn, advance turn and wait
		success = engine.end_turn()
		
		if not success:
			print(f"Replay error: Could not end turn {turn} — required choices missing")
			break  # or raise Exception or log error

		time.sleep(1.0 / speed)

