
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

	def run(self):
		screen, clock, font, big_font, terrain_overlays, resource_icons, unit_icons = helper.init_pygame_assets()

		for turn in sorted(self.actions_by_turn.keys()):
			for action_type, data in self.actions_by_turn[turn]:
				handle_action(self.engine, action_type, data, False)

				# === Rendering ===
				BASE_WIDTH = constants.WIDTH
				BASE_HEIGHT = constants.HEIGHT				

				window_width, window_height = pygame.display.get_surface().get_size()
				scale = min(window_width / BASE_WIDTH, window_height / BASE_HEIGHT)
				scaled_width = int(BASE_WIDTH * scale)
				scaled_height = int(BASE_HEIGHT * scale)
				x_offset = (window_width - scaled_width) // 2
				y_offset = (window_height - scaled_height) // 2

				mx, my = pygame.mouse.get_pos()
				adjusted_mx = mx - x_offset
				adjusted_my = my - y_offset
				logical_mx = adjusted_mx / scale if scale != 0 else adjusted_mx
				logical_my = adjusted_my / scale if scale != 0 else adjusted_my
				logical_mx = max(0, min(BASE_WIDTH - 1, logical_mx))
				logical_my = max(0, min(BASE_HEIGHT - 1, logical_my))
				pos = (int(logical_mx), int(logical_my))

				base_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
				base_surface.fill((255, 255, 255))
				hex_mask = helper.create_hex_mask(constants.HEX_RADIUS)
				self.renderer.draw_grid(base_surface, self.engine, font, big_font, terrain_overlays, hex_mask, resource_icons)
				self.renderer.draw_territory_shading(base_surface, self.engine, font, big_font)
				self.renderer.draw_cities(base_surface, self.engine, font, big_font)
				self.renderer.draw_units(base_surface, self.engine, font, big_font, unit_icons)
				self.renderer.draw_ui(base_surface, self.engine, font, big_font, resource_icons)
				self.renderer.draw_message(base_surface, self.engine)

				scaled_surface = pygame.transform.smoothscale(base_surface, (scaled_width, scaled_height))
				screen.fill((0, 0, 0))
				screen.blit(scaled_surface, (x_offset, y_offset))

				pygame.display.flip()
				time.sleep(0.05 / self.speed)

			success = self.engine.end_turn()
			if not success:
				print(f"Replay error: Could not end turn {turn} — required choices missing")
				break

			time.sleep(1.0 / self.speed)
