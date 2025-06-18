
import pygame
import random
import json
import math
import time
import renderer
import os
import dictionary
import copy
import helper
import player
import core
import systems
from engine import Engine
from constants import GRID_WIDTH, GRID_HEIGHT, HEX_RADIUS, WIDTH, HEIGHT, FPS, CITY_NAMES

def main():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Civ V Build Order Optimizer")
	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 20)
	big_font = pygame.font.SysFont(None, 24)
	
	hovered_tile_coords = None
	hover_start_time = 0
	HOVER_DELAY = 0.2  # seconds
 
	terrain_overlays = {}
	
	for filename in os.listdir("assets"):
		if filename.endswith(".png"):
			key = filename[:-4]  # Strip ".png" to get the base name
			image = pygame.image.load(os.path.join("assets", filename)).convert_alpha()
			terrain_overlays[key] = image

	unit_icons = helper.load_unit_icons()

	try:
		pygame.mixer.init()
		pygame.mixer.music.load('gandhi.mp3')  # replace with your file name/path
		pygame.mixer.music.play(-1)  # loop indefinitely
	except Exception as e:
		print(f"Could not load or play music: {e}")

	engine = Engine()
	running = True

	while running:
		clock.tick(FPS)
		if engine.message_timer > 0:
			engine.message_timer -= 1

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			elif event.type == pygame.MOUSEBUTTONDOWN:
				mx, my = pygame.mouse.get_pos()
				pos = (mx, my)

				# Handle tech buttons
				for btn in engine.ui_tech_buttons:
					if btn["rect"].collidepoint(pos):
						tech = btn["tech"]
						tech_name = btn["tech_name"]
						if not tech.unlocked and tech.can_research(engine.current_player.science_system.get_unlocked_names()):
							engine.current_player.science_system.set_current_research(tech_name)
							engine.show_message(f"Selected tech: {tech_name}", 90)
						elif not tech.can_research(engine.current_player.science_system.get_unlocked_names()):
							engine.show_message(f"Can't research {tech_name} yet — missing prerequisites.", 90)
						break

				# Handle policy buttons
				for btn in engine.ui_policy_buttons:
					if btn["rect"].collidepoint(pos):
						if not btn["is_unlocked"] and btn["can_afford"]:
							success = engine.current_player.choose_policy(btn["policy"], engine)
							if success:
								pass
						break

				# Handle Found City button
				if engine.ui_found_city_button and engine.ui_found_city_button.collidepoint(pos):
					if engine.selected_unit and engine.selected_unit.name == "Settler":
						engine.found_city(engine.selected_unit)

				# Handle End Turn button
				if engine.ui_next_turn_button and engine.ui_next_turn_button.collidepoint(pos):
					engine.end_turn()

				# Handle grid clicks
				hex_coords = helper.get_hex_at_pixel(mx, my)
				if hex_coords:
					q, r = hex_coords
					if event.button == 1:  # Left click
						unit = engine.get_unit_at(q, r)
						city = engine.get_city_at(q, r)
						if unit:
							engine.selected_unit = unit
							engine.selected_city = None
						elif city:
							engine.selected_city = city
							engine.selected_unit = None
						else:
							engine.selected_unit = None
							engine.selected_city = None
					elif event.button == 3:  # Right click
						hex_coords = helper.get_hex_at_pixel(mx, my)
						if hex_coords:
							q, r = hex_coords
							# Make sure the tile exists
							if 0 <= q < GRID_WIDTH and 0 <= r < GRID_HEIGHT:
								tile = engine.tiles[q][r]

								if engine.selected_unit:
									unit = engine.selected_unit
									from_tile = engine.tiles[unit.q][unit.r]
									result = unit.move_to(from_tile, tile)
									if result is not True:
										engine.show_message(result, 90)
									else:
										helper.check_proximity_rewards(engine, engine.current_player)


								elif engine.selected_city:
									city = engine.selected_city

									if helper.can_purchase_tile(city, tile, engine):
										cost = helper.get_tile_purchase_cost(city, tile)
										if engine.current_player.gold >= cost:
											tile.owner = engine.current_player
											city.border.append((q, r))
											engine.current_player.gold -= cost
											engine.show_message(f"Tile purchased for {cost}g!", 90)
										else:
											engine.show_message("Not enough gold to purchase tile.", 90)
									else:
										engine.show_message("Can't buy this tile. Not adjacent or out of range.", 90)
							else:
								engine.show_message("Clicked outside map bounds.", 90)
						else:
							engine.show_message("Invalid tile.", 90)


				# Handle purchase buttons (units/buildings)
				for btn in engine.ui_purchase_buttons:
					if btn["rect"].collidepoint(pos):
						itype = btn["type"]
						name = btn["name"]
						cost = btn["cost"]

						player = engine.current_player

						if player.gold >= cost:
							if itype == "building":
								success, message = engine.selected_city.purchase_building(name, player)
								engine.show_message(message, 90)

							elif itype == "unit":
								success, message = engine.selected_city.purchase_unit(name, player)
								if success:
									engine.show_message(message, 90)

						else:
							engine.show_message("Not enough gold to purchase.", 90)

						break  # Stop checking other buttons once one clicked

				for btn in engine.ui_production_buttons:
					if btn["rect"].collidepoint(pos):
						project = btn["project"]
						success = engine.selected_city.production_system.start_project(project)
						if success:
							engine.show_message(f"Started building {project.name}", 90)
						else:
							engine.show_message(f"Cannot build {project.name}", 90) #better error msgs
						break

				# Handle Pantheon buttons
				for btn in engine.ui_pantheon_buttons:
					if btn["rect"].collidepoint(pos):
						pantheon_name = btn["pantheon_name"]
						pantheon_data = btn["pantheon_data"]
						if engine.current_player.pantheon is None:
							engine.current_player.pantheon = pantheon_name
							engine.taken_pantheons.append(pantheon_name)
							engine.show_message(f"Chosen Pantheon: {pantheon_name}", 120)
						break

		screen.fill((255, 255, 255))
		hex_mask = helper.create_hex_mask(HEX_RADIUS)
		renderer.draw_grid(screen, engine, font, big_font, terrain_overlays, hex_mask)
		renderer.draw_territory_shading(screen, engine, font, big_font)
		renderer.draw_cities(screen, engine, font, big_font)
		renderer.draw_units(screen, engine, font, big_font, unit_icons)
		renderer.draw_ui(screen, engine, font, big_font)
		renderer.draw_message(screen, engine)

		# --- Tile Hover Info UI ---
		mx, my = pygame.mouse.get_pos()
		hex_coords = helper.get_hex_at_pixel(mx, my)

		if hex_coords:
			q, r = hex_coords
			if hovered_tile_coords != (q, r):
				hovered_tile_coords = (q, r)
				hover_start_time = time.time()

			# Only show info if hovered for more than 0.5s
			if time.time() - hover_start_time >= HOVER_DELAY:
				tile = engine.tiles[q][r]

				terrain_name = dictionary.TERRAIN_TYPES[tile.terrain_type]["name"]

				info_lines = [
					f"Tile: ({q}, {r})",  # 👈 Add tile coordinates here
					f"Terrain: {terrain_name}",
					f"Improvement: {tile.improvement or 'None'}",
					f"Resource: {tile.resource or 'None'}",
					f"Yield - Food: {tile.food}, Prod: {tile.production}, Gold: {tile.gold}"
				]

				info_width = 220
				info_height = 20 * len(info_lines)
				info_x = mx + 15
				info_y = my + 15

				pygame.draw.rect(screen, (240, 240, 240), (info_x, info_y, info_width, info_height))
				pygame.draw.rect(screen, (0, 0, 0), (info_x, info_y, info_width, info_height), 2)

				for i, line in enumerate(info_lines):
					text = font.render(line, True, (0, 0, 0))
					screen.blit(text, (info_x + 5, info_y + 5 + i * 20))
		else:
			hovered_tile_coords = None
			hover_start_time = 0

		pygame.display.flip()

	pygame.mixer.music.stop()
	pygame.mixer.quit()
	pygame.event.pump()
	pygame.quit()

if __name__ == "__main__":
	main()