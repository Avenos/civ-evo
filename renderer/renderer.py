
#here is renderer.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import math
import pygame
import os
import ctypes
import time
import numpy as np

from utils import helper
from data import dictionary, constants

class Renderer():
	def __init__(self, engine):
		pygame.display.init()
		pygame.font.init()

		self.engine = engine

		self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
		pygame.display.set_caption("Civ V Build Order Optimizer")

		# Maximize the window (Windows only)
		hwnd = pygame.display.get_wm_info()["window"]
		ctypes.windll.user32.ShowWindow(hwnd, 3)

		self.font = pygame.font.SysFont(None, 20)
		self.big_font = pygame.font.SysFont(None, 24)
		self.base_surface = pygame.Surface((constants.WIDTH, constants.HEIGHT))
		self.base_surface.fill((255, 255, 255))
		self.hex_mask = helper.create_hex_mask(constants.HEX_RADIUS)		

		self.yield_types = ["food", "production", "gold", "science", "culture", "faith", "happiness", "unhappiness"]
		self.icon_images = {}
		for yield_type in self.yield_types:
			self.icon_images[yield_type] = pygame.image.load(f"assets/icons/{yield_type}.png").convert_alpha()		

		from .render_ui import RenderUI
		from .render_utils import RenderUtils		

		self.ui = RenderUI(self)
		self.utils = RenderUtils(self)
		self.scale = 1.0
		self.x_offset = 0
		self.y_offset = 0

	def update_dimensions(self):
		window_width, window_height = pygame.display.get_surface().get_size()
		self.scale = min(window_width / constants.WIDTH, window_height / constants.HEIGHT)
		self.scaled_width = int(constants.WIDTH * self.scale)
		self.scaled_height = int(constants.HEIGHT * self.scale)
		self.x_offset = (window_width - self.scaled_width) // 2
		self.y_offset = (window_height - self.scaled_height) // 2

	def get_logical_mouse_pos(self):
		mx, my = pygame.mouse.get_pos()
		adjusted_mx = mx - self.x_offset
		adjusted_my = my - self.y_offset
		if self.scale != 0:
			logical_mx = adjusted_mx / self.scale
			logical_my = adjusted_my / self.scale
		else:
			logical_mx = adjusted_mx
			logical_my = adjusted_my

		logical_mx = max(0, min(constants.WIDTH - 1, logical_mx))
		logical_my = max(0, min(constants.HEIGHT - 1, logical_my))
		return (int(logical_mx), int(logical_my))		

	def render(self):
		self.update_dimensions()

		self.base_surface.fill(constants.WHITE)
		self.hex_mask = helper.create_hex_mask(constants.HEX_RADIUS)  # store in self if reused

		self.utils.draw_grid()
		self.utils.draw_territory_shading()
		self.utils.draw_cities()
		self.utils.draw_units()
		self.ui.draw_ui()
		self.utils.draw_message()

		scaled_surface = pygame.transform.smoothscale(
			self.base_surface,
			(self.scaled_width, self.scaled_height)
		)
		self.screen.fill(constants.BLACK)
		self.screen.blit(scaled_surface, (self.x_offset, self.y_offset))

		pygame.display.flip()


		## Hover tooltip
		#hovered_tile_coords = None
		#hover_start_time = 0
		#HOVER_DELAY = 0.2  # seconds

		#hex_coords = helper.get_hex_at_pixel(logical_mx, logical_my)
		#if hex_coords:
			#q, r = hex_coords
			#if hovered_tile_coords != (q, r):
				#hovered_tile_coords = (q, r)
				#hover_start_time = time.time()
			#if time.time() - hover_start_time >= HOVER_DELAY:
				#tile = self.engine.tiles[q][r]
				#info_lines = [
					#f"Tile: ({q}, {r})",
					#f"Terrain: {tile.terrain_type}",
					#f"Trees: {tile.trees}",
					#f"Improvement: {tile.improvement or 'None'}",
				#]

				## Show improvement progress if under construction
				#if tile.improvement and tile.improvement_progress is not None:
					## Default to 3 if you want a safe fallback
					#progress = tile.improvement_progress
					## Estimate total turns if available this is very bad.....
					#base_turns = {
						#"Farm": 3,
						#"Mine": 3,
						#"Road": 3,
						#"Pasture": 3,
						#"Plantation": 3,
						#"Quarry": 3,
						#"Camp": 3,
						#}.get(tile.improvement, 3)
					#info_lines.append(f"Progress: {progress}/{base_turns}")

				##only show if not zero
				#info_lines += [
					#f"Resource: {tile.resource or 'None'}",
					#f"Fresh water: {tile.fresh_water}",
					#f"Food: {tile.food}",
					#f"Production: {tile.production}",
					#f"Science: {tile.science}",
					#f"Gold: {tile.gold}",
					#f"Culture: {tile.culture}",
					#f"Faith: {tile.faith}",
				#]

				#info_width = 220
				#info_height = 20 * len(info_lines)
				#info_x = mx + 15
				#info_y = my + 15
				#pygame.draw.rect(self.screen, (240, 240, 240), (info_x, info_y, info_width, info_height))
				#pygame.draw.rect(self.screen, constants.BLACK, (info_x, info_y, info_width, info_height), 2)
				#for i, line in enumerate(info_lines):
					#text = self.font.render(line, True, (0, 0, 0))
					#self.screen.blit(text, (info_x + 5, info_y + 5 + i * 20))
		#else:
			#hovered_tile_coords = None
			#hover_start_time = 0

		#pygame.display.flip()		
