import json
import time
import pygame
from collections import defaultdict
import os

from data import constants
from engine import handle_action
from renderer import Renderer
from utils import helper

class Replay:
	def __init__(self, replay_filename, engine, speed=1.0):
		self.engine = engine
		
		self.speed = speed
		self.actions_by_turn = defaultdict(list)
		self.current_turn = 0
		self.renderer = Renderer()  # Moved here

		# Load replay file
		replay_path = os.path.join('replays', replay_filename)
		if not os.path.isfile(replay_path):
			raise FileNotFoundError(f"Replay file not found in 'replays': {replay_filename}")

		with open(replay_path, 'r') as f:
			actions = json.load(f)

		for turn, action_type, data in actions:
			self.actions_by_turn[turn].append((action_type, data))

		# Pygame assets setup
		(self.screen, self.clock, self.font, self.big_font,
		 self.terrain_overlays, self.resource_icons, self.unit_icons) = helper.init_pygame_assets()

	def play(self):
		for turn in sorted(self.actions_by_turn.keys()):
			for action_type, data in self.actions_by_turn[turn]:
				handle_action(self.engine, action_type, data, False)

				self.screen.fill((255, 255, 255))
				hex_mask = helper.create_hex_mask(constants.HEX_RADIUS)

				self.renderer.draw_grid(self.screen, self.engine, self.font, self.big_font, self.terrain_overlays, hex_mask, self.resource_icons)
				self.renderer.draw_territory_shading(self.screen, self.engine, self.font, self.big_font)
				self.renderer.draw_cities(self.screen, self.engine, self.font, self.big_font)
				self.renderer.draw_units(self.screen, self.engine, self.font, self.big_font, self.unit_icons)
				self.renderer.draw_ui(self.screen, self.engine, self.font, self.big_font, self.resource_icons)
				self.renderer.draw_message(self.screen, self.engine)

				pygame.display.flip()
				time.sleep(0.05 / self.speed)

			success = self.engine.end_turn()
			if not success:
				print(f"Replay error: Could not end turn {turn} — required choices missing")
				break

			time.sleep(1.0 / self.speed)
