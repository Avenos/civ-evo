
#here is random_agent.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import random
import pygame
import time

from data import dictionary, constants
from engine import Engine, handle_action, start_new_log
from renderer import Renderer
from utils import helper

class RandomAgent:
	def __init__(self, engine, headless=True):
		self.engine = engine
		self.renderer = Renderer()
		self.headless = headless

	def run(self):
		screen, clock, font, big_font, terrain_overlays, resource_icons, unit_icons = helper.init_pygame_assets(headless=self.headless)

		#start_new_log(self.engine)
		BASE_WIDTH = constants.WIDTH
		BASE_HEIGHT = constants.HEIGHT
		running = True

		while running:
			clock.tick(constants.FPS)

			if not self.headless:
				for event in pygame.event.get():
					if event.type == pygame.QUIT:
						running = False

			if self.engine.message_timer > 0:
				self.engine.message_timer -= 1

			legal_actions = self.engine.get_legal_actions(self.engine.current_player)
			if not legal_actions:
				break  # Safety guard

			action = random.choice(legal_actions)
			handle_action(self.engine, action["action"], action["data"], False)

			if self.headless:
				continue  # Skip rendering

			# === Rendering ===
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
			pygame.time.wait(50)

		if not self.headless:
			pygame.quit()
