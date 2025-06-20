
import json
import time
import pygame
import renderer
import helper
import os
from constants import HEX_RADIUS
from collections import defaultdict

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


def handle_action(engine, action_type, data):
	"""
	Handles a single action applied to the engine.
	Expand this as needed for your game logic.
	"""


	if action_type == "move_unit":
		unit = engine.get_unit_by_id(data["unit_id"])
		to_q, to_r = data["to"]
		if unit:
			from_tile = engine.tiles[unit.q][unit.r]
			to_tile = engine.tiles[to_q][to_r]
			result = unit.move_to(from_tile, to_tile)
			if result is not None:
				print(f"Replay error: {result}")
				return False
			return True

	elif action_type == "found_city":
		unit = engine.get_unit_by_id(data["unit_id"])
		if unit:
			engine.current_player.found_city(unit, engine)

	elif action_type == "choose_production":
		city = engine.get_city_by_id(data["city_id"])
		if city:
			city.production_system.set_current_project(data["name"])

	#elif action_type == "purchase_unit":
		#city = engine.get_city_by_id(data["city_id"])
		#if city:
			#city.purchase_unit(data["name"], engine.current_player)

	#elif action_type == "select_policy":
		#policy = data["policy"]
		#engine.current_player.choose_policy(policy, engine)

	#elif action_type == "select_tech":
		#tech_name = data["tech"]
		#engine.current_player.science_system.set_current_research(tech_name)

	elif action_type == "end_turn":
		engine.end_turn()

	# Add more action handlers as needed