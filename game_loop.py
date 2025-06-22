
import pygame
import random
import json
import math
import time
import renderer
import os
import sys
import dictionary
import copy
import helper
import player
import core
import systems
import game_loop
from action_handler import handle_action, start_new_replay_log
from engine import Engine
from constants import GRID_WIDTH, GRID_HEIGHT, HEX_RADIUS, WIDTH, HEIGHT, FPS, CITY_NAMES

def run_manual_game(engine):
	screen, clock, font, big_font, terrain_overlays, resource_icons, unit_icons = helper.init_pygame_assets()

	start_new_replay_log(engine)
	hovered_tile_coords = None
	hover_start_time = 0
	HOVER_DELAY = 0.2  # seconds

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
						tech_name = btn["tech_name"]
						success, message = handle_action(engine, "set_research", {"tech_name": tech_name})
						engine.show_message(message if not success else f"Selected tech: {tech_name}", 90)
						break

				# Handle policy buttons
				for btn in engine.ui_policy_buttons:
					if btn["rect"].collidepoint(pos):
						policy_name = btn["policy"]
						success, message = handle_action(engine, "choose_policy", {"policy_name": policy_name})
						engine.show_message(message if not success else f"Policy chosen: {policy_name}", 90)
						break

				if engine.ui_found_city_button and engine.ui_found_city_button.collidepoint(pos):
					if engine.selected_unit:
						unit_id = engine.selected_unit.id
						success, message = handle_action(engine, "found_city", {"unit_id": unit_id})
						engine.show_message(message if not success else "City founded!", 90)
						break

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
							if 0 <= q < GRID_WIDTH and 0 <= r < GRID_HEIGHT:
								tile = engine.tiles[q][r]

								if engine.selected_unit:
									unit_id = engine.selected_unit.id
									action_data = {"unit_id": unit_id, "to": (q, r)}
									success, message = handle_action(engine, "move_unit", action_data)
									if not success:
										engine.show_message(message, 90)
									else:
										helper.check_proximity_rewards(engine, engine.current_player)

								elif engine.selected_city:
									city_id = engine.selected_city.id
									action_data = {"city_id": city_id, "tile_coords": (q, r)}
									success, message = handle_action(engine, "purchase_tile", action_data)
									engine.show_message(message if not success else f"Tile purchased!", 90)
							else:
								engine.show_message("Clicked outside map bounds.", 90)
						else:
							engine.show_message("Invalid tile.", 90)


				# Handle purchase buttons (units/buildings)
				for btn in engine.ui_purchase_buttons:
					if btn["rect"].collidepoint(pos):
						itype = btn["type"]
						name = btn["name"]
						city_id = engine.selected_city.id if engine.selected_city else None

						if city_id is not None:
							action_type = "purchase_building" if itype == "building" else "purchase_unit"
							success, message = handle_action(engine, action_type, {
								"city_id": city_id,
								"name": name
							})
							engine.show_message(message if not success else f"Purchased {name}", 90)
						else:
							engine.show_message("No city selected.", 90)

						break  # Stop checking other buttons once one clicked

				for btn in engine.ui_production_buttons:
					if btn["rect"].collidepoint(pos):
						project = btn["project"]
						city_id = engine.selected_city.id if engine.selected_city else None
						if city_id is not None:
							success, message = handle_action(engine, "choose_project", {
								"city_id": city_id,
								"project_name": project.name
							})
							engine.show_message(message if not success else f"Started building {project.name}", 90)
						else:
							engine.show_message("No city selected.", 90)
						break

				# Handle Pantheon buttons
				for btn in engine.ui_pantheon_buttons:
					if btn["rect"].collidepoint(pos):
						pantheon_name = btn["pantheon_name"]
						success, message = handle_action(engine, "choose_pantheon", {"pantheon_name": pantheon_name})
						engine.show_message(message if not success else f"Chose pantheon: {pantheon_name}", 120)
						break


		screen.fill((255, 255, 255))
		hex_mask = helper.create_hex_mask(HEX_RADIUS)
		renderer.draw_grid(screen, engine, font, big_font, terrain_overlays, hex_mask, resource_icons)
		renderer.draw_territory_shading(screen, engine, font, big_font)
		renderer.draw_cities(screen, engine, font, big_font)
		renderer.draw_units(screen, engine, font, big_font, unit_icons)
		renderer.draw_ui(screen, engine, font, big_font, resource_icons)
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
					f"Tile: ({q}, {r})",
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

	pygame.quit()