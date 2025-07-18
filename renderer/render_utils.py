
import os
import pygame
import numpy as np
import math

from data import constants
from utils import helper

class RenderUtils():
	def __init__(self, renderer):
		self.renderer = renderer
		self.engine = renderer.engine
		
		self.terrain_overlays = {}
		for filename in os.listdir("assets"):
			if filename.endswith(".png"):
				key = filename[:-4]
				image = pygame.image.load(os.path.join("assets", filename)).convert_alpha()
				self.terrain_overlays[key] = image
	
		self.unit_icons = {}
		for filename in os.listdir("assets/units"):
			if filename.lower().endswith(".png"):
				unit_name = os.path.splitext(filename)[0].lower()
				full_path = os.path.join("assets/units", filename)
				unit_icon = pygame.image.load(full_path).convert_alpha()
				self.unit_icons[unit_name] = unit_icon
				
	def blit_hex_overlay_clipped(self, overlay_img, center_x, center_y):
		overlay_scaled = pygame.transform.smoothscale(overlay_img, (constants.HEX_DIAMETER, constants.HEX_DIAMETER))
	
		temp_surf = pygame.Surface((constants.HEX_DIAMETER, constants.HEX_DIAMETER), pygame.SRCALPHA)
	
		temp_surf.blit(overlay_scaled, (0, 0))
	
		overlay_alpha = pygame.surfarray.pixels_alpha(temp_surf)
		mask_alpha = pygame.surfarray.pixels_alpha(self.renderer.hex_mask)
	
		overlay_alpha[:] = (overlay_alpha * (mask_alpha / 255.0)).astype(np.uint8)
	
		del overlay_alpha, mask_alpha
	
		top_left_x = center_x - constants.HEX_RADIUS
		top_left_y = center_y - constants.HEX_RADIUS
	
		self.renderer.base_surface.blit(temp_surf, (top_left_x, top_left_y))
	
	def draw_hex(self, x, y, color, width=2):
		points = []
		for i in range(6):
			angle = math.radians(60 * i - 30)  # shift by -30 degrees for pointy-top
			px = x + constants.HEX_RADIUS * math.cos(angle)
			py = y + constants.HEX_RADIUS * math.sin(angle)
			points.append((px, py))
		pygame.draw.polygon(self.renderer.base_surface, color, points, width)
	
	def draw_grid(self):
		for q in range(constants.GRID_WIDTH):
			for r in range(constants.GRID_HEIGHT):
				x, y = helper.hex_to_pixel(q, r)
				tile = self.engine.tiles[q][r]
	
				key = helper.build_tile_image_key(tile, self.terrain_overlays.keys())
				img = self.terrain_overlays.get(key)
	
				if img:
					self.blit_hex_overlay_clipped(img, x, y)
				else:
					base_img = self.terrain_overlays.get(tile.terrain_type.lower())
					if base_img:
						blit_hex_overlay_clipped(self.renderer.screen, base_img, x, y, hex_mask)
					else:
						points = [helper.get_hex_corner(x, y, i) for i in range(6)]
						pygame.draw.polygon(screen, constants.BLACK, points)
	
				# Draw ancient ruin
				if tile.ancient_ruin:
					ar_text = "AR"
					ar_surf = self.renderer.font.render(ar_text, True, (139, 69, 19))
					ar_rect = ar_surf.get_rect(center=(x, y + constants.HEX_RADIUS // 2))
					self.renderer.base_surface.blit(ar_surf, ar_rect)
	
					# --- Draw tile yield icons ---
					yield_offset_x = -20  # Adjust horizontal spacing between icons
					yield_offset_y = constants.HEX_RADIUS // 3  # Slightly below center of tile
	
				icon_spacing = 16
				yield_offset_x = -10
				yield_offset_y = constants.HEX_RADIUS // 3
				current_x = x + yield_offset_x
	
				for attr in ["food", "production", "gold", "science", "culture", "faith"]:
					amount = getattr(tile, attr, 0)
					if amount > 0:
						icon = self.renderer.icon_images.get(attr)
						if icon:
							for _ in range(amount):
								icon_rect = icon.get_rect(midbottom=(current_x, y + yield_offset_y))
								self.renderer.base_surface.blit(icon, icon_rect)
								current_x += icon_spacing
	
							# Draw hex border
							self.draw_hex(x, y, constants.BLACK)
	
							# Draw rivers
							for edge_index in tile.rivers:
								start = helper.get_hex_corner(x, y, edge_index)
								end = helper.get_hex_corner(x, y, (edge_index + 1) % 6)
								pygame.draw.line(screen, CYAN, start, end, 5)						
	
	def draw_territory_shading(self):
		territory_surf = pygame.Surface((constants.WIDTH, constants.HEIGHT), pygame.SRCALPHA)
	
		for row in self.engine.tiles:
			for tile in row:
				if tile.owner:
					# Your polygon points calculation unchanged
					player_index = self.engine.players.index(tile.owner)
					x, y = helper.hex_to_pixel(tile.q, tile.r)
					points = []
					for i in range(6):
						angle = math.radians(60 * i - 30)
						px = x + constants.HEX_RADIUS * math.cos(angle)
						py = y + constants.HEX_RADIUS * math.sin(angle)
						points.append((px, py))
					pygame.draw.polygon(territory_surf, (0, 200, 0, 50), points)
	
		# Blit this onto the base surface, NOT screen
		self.renderer.base_surface.blit(territory_surf, (0, 0))

	def draw_cities(self):
		for player in self.engine.players:
			for city in player.cities:
				x, y = helper.hex_to_pixel(city.q, city.r)
	
				# Draw a big red circle behind the city population number for visibility
				pygame.draw.circle(self.renderer.screen, constants.RED, (int(x), int(y)), 18)
	
				# Draw city population number in white on top
				label = self.renderer.big_font.render(str(city.population), True, constants.WHITE)
				label_rect = label.get_rect(center=(x, y))
				self.renderer.base_surface.blit(label, label_rect)
	
				# Optionally, draw a simple city icon (if you have one)
				# city_icon = some_surface_loaded_earlier
				# icon_rect = city_icon.get_rect(center=(x, y + 20))  # slightly below number
				# self.renderer.base_surface.blit(city_icon, icon_rect)
	
				# Only draw worked tile dots if this city is selected
				if self.engine.selected_city == city:
					for tile in city.worked_tiles:
						if (tile.q, tile.r) == (city.q, city.r):
							continue  # skip city tile itself
						wx, wy = helper.hex_to_pixel(tile.q, tile.r)
						pygame.draw.circle(self.renderer.screen, constants.DARK_YELLOW, (int(wx), int(wy)), 6)
	
	def draw_units(self):
		ICON_SIZE = 40  # or smaller, e.g., 16
	
		for unit in self.engine.current_player.units:
			x, y = helper.hex_to_pixel(unit.q, unit.r)
			selected = (unit == self.engine.selected_unit)
	
			if selected:
				self.draw_hex(x, y, constants.GREEN, width=3)
	
			icon = self.unit_icons.get(unit.name.lower())  # or however you key them
			if icon:
				scaled_icon = pygame.transform.smoothscale(icon, (ICON_SIZE, ICON_SIZE))
				icon_rect = scaled_icon.get_rect(center=(x, y))
				self.renderer.base_surface.blit(scaled_icon, icon_rect)
			else:
				# fallback to text label if icon missing
				color = constants.GREEN if selected else constants.BLUE
				label = self.renderer.big_font.render(unit.name, True, color)
				label_rect = label.get_rect(center=(x, y))
				self.renderer.base_surface.blit(label, label_rect)
	
	def draw_message(self):
		if self.engine.message_timer > 0 and self.engine.message:
			self.renderer.font = pygame.font.SysFont("arial", 18)
			text_surface = self.renderer.font.render(self.engine.message, True, (255, 255, 255))
			background = pygame.Surface((text_surface.get_width() + 20, text_surface.get_height() + 10))
			background.set_alpha(180)
			background.fill(constants.BLACK)
			self.renderer.base_surface.blit(background, (10, 10))
			self.renderer.base_surface.blit(text_surface, (20, 15))
