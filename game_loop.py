
import pygame
import time
import helper
import renderer
from dictionary import TERRAIN_TYPES
from action_handler import handle_action, start_new_log
from engine import Engine
from constants import GRID_WIDTH, GRID_HEIGHT, HEX_RADIUS, WIDTH, HEIGHT, FPS, CITY_NAMES

import pygame
import time
import helper
import renderer
from dictionary import TERRAIN_TYPES
from action_handler import handle_action, start_new_log
from engine import Engine
from constants import GRID_WIDTH, GRID_HEIGHT, HEX_RADIUS, WIDTH, HEIGHT, FPS, CITY_NAMES

def run_manual_game(engine):
	screen, clock, font, big_font, terrain_overlays, resource_icons, unit_icons = helper.init_pygame_assets()

	start_new_log(engine)
	hovered_tile_coords = None
	hover_start_time = 0
	HOVER_DELAY = 0.2  # seconds

	running = True

	BASE_WIDTH = WIDTH
	BASE_HEIGHT = HEIGHT

	while running:
		clock.tick(FPS)
		if engine.message_timer > 0:
			engine.message_timer -= 1

		window_width, window_height = pygame.display.get_surface().get_size()
		scale = min(window_width / BASE_WIDTH, window_height / BASE_HEIGHT)
		scaled_width = int(BASE_WIDTH * scale)
		scaled_height = int(BASE_HEIGHT * scale)
		x_offset = (window_width - scaled_width) // 2
		y_offset = (window_height - scaled_height) // 2

		mx, my = pygame.mouse.get_pos()
		adjusted_mx = mx - x_offset
		adjusted_my = my - y_offset
		if scale != 0:
			logical_mx = adjusted_mx / scale
			logical_my = adjusted_my / scale
		else:
			logical_mx = adjusted_mx
			logical_my = adjusted_my

		logical_mx = max(0, min(BASE_WIDTH - 1, logical_mx))
		logical_my = max(0, min(BASE_HEIGHT - 1, logical_my))
		pos = (int(logical_mx), int(logical_my))

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			elif event.type == pygame.MOUSEBUTTONDOWN:
				logical_click_handled = False

				for btn in engine.ui_tech_buttons:
					if btn["rect"].collidepoint(pos):
						tech_name = btn["tech_name"]
						success, message = handle_action(engine, "set_research", {"tech_name": tech_name})
						engine.show_message(message if not success else f"Selected tech: {tech_name}", 90)
						logical_click_handled = True
						break

				if not logical_click_handled:
					for btn in engine.ui_policy_buttons:
						if btn["rect"].collidepoint(pos):
							policy_name = btn["policy"]
							success, message = handle_action(engine, "choose_policy", {"policy_name": policy_name})
							engine.show_message(message if not success else f"Policy chosen: {policy_name}", 90)
							logical_click_handled = True
							break

				if not logical_click_handled and engine.ui_found_city_button and engine.ui_found_city_button.collidepoint(pos):
					if engine.selected_unit:
						unit_id = engine.selected_unit.id
						success, message = handle_action(engine, "found_city", {"unit_id": unit_id})
						engine.show_message(message if not success else "City founded!", 90)
					logical_click_handled = True

				elif not logical_click_handled and engine.ui_next_turn_button and engine.ui_next_turn_button.collidepoint(pos):
					engine.end_turn()
					logical_click_handled = True

				if not logical_click_handled:
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
							logical_click_handled = True
							break

				if not logical_click_handled:
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
							logical_click_handled = True
							break

				if not logical_click_handled:
					for btn in engine.ui_pantheon_buttons:
						if btn["rect"].collidepoint(pos):
							pantheon_name = btn["pantheon_name"]
							success, message = handle_action(engine, "choose_pantheon", {"pantheon_name": pantheon_name})
							engine.show_message(message if not success else f"Chose pantheon: {pantheon_name}", 120)
							logical_click_handled = True
							break

				if not logical_click_handled:
					hex_coords = helper.get_hex_at_pixel(logical_mx, logical_my)
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

						elif event.button == 3:  # Right click to buy tile
							if 0 <= q < GRID_WIDTH and 0 <= r < GRID_HEIGHT:
								tile = engine.tiles[q][r]
								if engine.selected_unit:
									unit_id = engine.selected_unit.id
									action_data = {"unit_id": unit_id, "to": (q, r)}
									success, message = handle_action(engine, "move_unit", action_data)
									if not success:
										engine.show_message(message, 90)
									else:
										helper.check_city_state_proximity(engine, engine.current_player)
								elif engine.selected_city:
									city_id = engine.selected_city.id
									action_data = {"city_id": city_id, "tile_coords": (q, r)}
									success, message = handle_action(engine, "purchase_tile", action_data)
									engine.show_message(message if not success else f"Tile purchased!", 90)
							else:
								engine.show_message("Clicked outside map bounds.", 90)
					else:
						engine.show_message("Invalid tile.", 90)

		base_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
		base_surface.fill((255, 255, 255))
		hex_mask = helper.create_hex_mask(HEX_RADIUS)
		renderer.draw_grid(base_surface, engine, font, big_font, terrain_overlays, hex_mask, resource_icons)
		renderer.draw_territory_shading(base_surface, engine, font, big_font)
		renderer.draw_cities(base_surface, engine, font, big_font)
		renderer.draw_units(base_surface, engine, font, big_font, unit_icons)
		renderer.draw_ui(base_surface, engine, font, big_font, resource_icons)
		renderer.draw_message(base_surface, engine)

		scaled_surface = pygame.transform.smoothscale(base_surface, (scaled_width, scaled_height))
		screen.fill((0, 0, 0))  # Letterbox
		screen.blit(scaled_surface, (x_offset, y_offset))

		# Hover tooltip
		hex_coords = helper.get_hex_at_pixel(logical_mx, logical_my)
		if hex_coords:
			q, r = hex_coords
			if hovered_tile_coords != (q, r):
				hovered_tile_coords = (q, r)
				hover_start_time = time.time()
			if time.time() - hover_start_time >= HOVER_DELAY:
				tile = engine.tiles[q][r]
				info_lines = [
					f"Tile: ({q}, {r})",
					f"Terrain: {tile.terrain_type}",
					f"Trees: {tile.trees}",
					f"Improvement: {tile.improvement or 'None'}",
					f"Resource: {tile.resource or 'None'}",
					f"Fresh water: {tile.fresh_water or 'None'}",
					f"Food: {tile.food}",
					f"Production: {tile.production}",
					f"Science: {tile.science}",
					f"Gold: {tile.gold}",
					f"Culture: {tile.culture}",
					f"Faith: {tile.faith}",
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
