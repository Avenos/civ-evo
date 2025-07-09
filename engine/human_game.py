
import pygame
import time
from data import dictionary, constants
from engine import Engine, handle_action, start_new_log
from renderer import Renderer
from utils import helper

class HumanGame:
	def __init__(self, engine):
		self.engine = engine
		self.renderer = Renderer()

	def run(self):
		screen, clock, font, big_font, terrain_overlays, resource_icons, unit_icons = helper.init_pygame_assets()

		start_new_log(self.engine)
		hovered_tile_coords = None
		hover_start_time = 0
		HOVER_DELAY = 0.2  # seconds

		running = True

		BASE_WIDTH = constants.WIDTH
		BASE_HEIGHT = constants.HEIGHT

		while running:
			clock.tick(constants.FPS)
			if self.engine.message_timer > 0:
				self.engine.message_timer -= 1

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

					for btn in self.engine.ui_tech_buttons:
						if btn["rect"].collidepoint(pos):
							tech_name = btn["tech_name"]
							success, message = handle_action(self.engine, "choose_research", {"tech_name": tech_name})
							self.engine.show_message(message if not success else f"Selected tech: {tech_name}", 90)
							logical_click_handled = True
							break

					if not logical_click_handled:
						for btn in self.engine.ui_policy_buttons:
							if btn["rect"].collidepoint(pos):
								policy_name = btn["policy"]
								success, message = handle_action(self.engine, "choose_policy", {"policy_name": policy_name})
								self.engine.show_message(message if not success else f"Policy chosen: {policy_name}", 90)
								logical_click_handled = True
								break

					if not logical_click_handled:
						for btn in self.engine.ui_tile_improvement_buttons:
							if btn["rect"].collidepoint(pos):
								if self.engine.selected_unit:
									unit_id = self.engine.selected_unit.id
									# Get the tile coords where the worker currently is
									tile_coords = (self.engine.selected_unit.q, self.engine.selected_unit.r)
									improvement = btn["improvement"]
									action_data = {
										"unit_id": unit_id,
										"tile_coords": tile_coords,
										"improvement": improvement
									}
									success, message = handle_action(self.engine, "improve_tile", action_data)
									self.engine.show_message(message, 90)
								else:
									self.engine.show_message("No unit selected.", 90)
								logical_click_handled = True
								break


					if not logical_click_handled and self.engine.ui_found_city_button and self.engine.ui_found_city_button.collidepoint(pos):
						if self.engine.selected_unit:
							unit_id = self.engine.selected_unit.id
							success, message = handle_action(self.engine, "found_city", {"unit_id": unit_id})
							self.engine.show_message(message if not success else "City founded!", 90)
						logical_click_handled = True

					elif not logical_click_handled and self.engine.ui_next_turn_button and self.engine.ui_next_turn_button.collidepoint(pos):
						success, message = handle_action(self.engine, "end_turn", {"player": "placeholder"} )
						self.engine.show_message(message if not success else f"Turn ended", 90)

						logical_click_handled = True

					if not logical_click_handled:
						for btn in self.engine.ui_purchase_buttons:
							if btn["rect"].collidepoint(pos):
								itype = btn["type"]
								name = btn["name"]
								city_id = self.engine.selected_city.id if self.engine.selected_city else None
								if city_id is not None:
									action_type = "purchase_building" if itype == "building" else "purchase_unit"
									success, message = handle_action(self.engine, action_type, {
										"city_id": city_id,
										"name": name
									})
									self.engine.show_message(message if not success else f"Purchased {name}", 90)
								else:
									self.engine.show_message("No city selected.", 90)
								logical_click_handled = True
								break

					if not logical_click_handled:
						for btn in self.engine.ui_production_buttons:
							if btn["rect"].collidepoint(pos):
								project = btn["project"]
								city_id = self.engine.selected_city.id if self.engine.selected_city else None
								if city_id is not None:
									success, message = handle_action(self.engine, "choose_project", {
										"city_id": city_id,
										"project_name": project.name
									})
									self.engine.show_message(message if not success else f"Started building {project.name}", 90)
								else:
									self.engine.show_message("No city selected.", 90)
								logical_click_handled = True
								break

					if not logical_click_handled:
						for btn in self.engine.ui_pantheon_buttons:
							if btn["rect"].collidepoint(pos):
								pantheon_name = btn["pantheon_name"]
								success, message = handle_action(self.engine, "choose_pantheon", {"pantheon_name": pantheon_name})
								self.engine.show_message(message if not success else f"Chose pantheon: {pantheon_name}", 120)
								logical_click_handled = True
								break

					if not logical_click_handled:
						hex_coords = helper.get_hex_at_pixel(logical_mx, logical_my)
						if hex_coords:
							q, r = hex_coords
							if event.button == 1:  # Left click
								unit = self.engine.get_unit_at(q, r)
								city = self.engine.get_city_at(q, r)
								if unit:
									self.engine.selected_unit = unit
									self.engine.selected_city = None
								elif city:
									self.engine.selected_city = city
									self.engine.selected_unit = None
								else:
									self.engine.selected_unit = None
									self.engine.selected_city = None

							elif event.button == 3:  # Right click to buy tile
								if 0 <= q < constants.GRID_WIDTH and 0 <= r < constants.GRID_HEIGHT:
									tile = self.engine.tiles[q][r]
									if self.engine.selected_unit:
										unit_id = self.engine.selected_unit.id
										action_data = {"unit_id": unit_id, "to": (q, r)}
										success, message = handle_action(self.engine, "move_unit", action_data)
										if not success:
											self.engine.show_message(message, 90)
										else:
											helper.check_city_state_proximity(self.engine, self.engine.current_player)
									elif self.engine.selected_city:
										city_id = self.engine.selected_city.id
										action_data = {"city_id": city_id, "tile_coords": (q, r)}
										success, message = handle_action(engine, "purchase_tile", action_data)
										self.engine.show_message(message if not success else f"Tile purchased!", 90)
								else:
									self.engine.show_message("Clicked outside map bounds.", 90)
						else:
							self.engine.show_message("Invalid tile.", 90)

			base_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
			base_surface.fill((255, 255, 255))
			hex_mask = helper.create_hex_mask(constants.HEX_RADIUS)

			self.renderer.draw_grid(base_surface, self.engine, font, big_font, terrain_overlays, hex_mask, resource_icons)
			self. renderer.draw_territory_shading(base_surface, self.engine, font, big_font)
			self.renderer.draw_cities(base_surface, self.engine, font, big_font)
			self.renderer.draw_units(base_surface, self.engine, font, big_font, unit_icons)
			self.renderer.draw_ui(base_surface, self.engine, font, big_font, resource_icons)
			self.renderer.draw_message(base_surface, self.engine)

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
					tile = self.engine.tiles[q][r]
					info_lines = [
						f"Tile: ({q}, {r})",
						f"Terrain: {tile.terrain_type}",
						f"Trees: {tile.trees}",
						f"Improvement: {tile.improvement or 'None'}",
					]
			
					# Show improvement progress if under construction
					if tile.improvement and tile.improvement_progress is not None:
						# Default to 3 if you want a safe fallback
						progress = tile.improvement_progress
						# Estimate total turns if available this is very bad.....
						base_turns = {
							"Farm": 3,
							"Mine": 3,
							"Road": 3,
							"Pasture": 3,
							"Plantation": 3,
							"Quarry": 3,
							"Camp": 3,
						}.get(tile.improvement, 3)
						info_lines.append(f"Progress: {progress}/{base_turns}")
			
					#only show if not zero
					info_lines += [
						f"Resource: {tile.resource or 'None'}",
						f"Fresh water: {tile.fresh_water}",
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
