
#here is human_game.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import pygame
import time
from data import dictionary, constants
from engine import Engine, handle_action, start_new_log
from renderer import Renderer
from utils import helper

class HumanGame:
	def __init__(self, engine):
		self.engine = engine
		self.renderer = Renderer(engine)

	def run(self):
		self.clock = clock = pygame.time.Clock()
		running = True
		
		while running:
			clock.tick(constants.FPS)
			
			pos = self.renderer.get_logical_mouse_pos()
			
			if self.engine.message_timer > 0:
				self.engine.message_timer -= 1

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False

				elif event.type == pygame.MOUSEBUTTONDOWN:
					logical_click_handled = False

					for btn in self.engine.ui_tech_buttons:
						if btn["rect"].collidepoint(pos):
							tech_name = btn["tech_name"]
							result = handle_action(self.engine, "choose_research", {"tech_name": tech_name})
							self.engine.show_message(result.message)
							logical_click_handled = True
							break

					if not logical_click_handled:
						for btn in self.engine.ui_policy_buttons:
							if btn["rect"].collidepoint(pos):
								policy_name = btn["policy"]
								result = handle_action(self.engine, "choose_policy", {"policy_name": policy_name})
								self.engine.show_message(result.message)
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
									result = handle_action(self.engine, "improve_tile", action_data)
									self.engine.show_message(result.message)
								else:
									self.engine.show_message("No unit selected.")
								logical_click_handled = True
								break


					if not logical_click_handled and self.engine.ui_found_city_button and self.engine.ui_found_city_button.collidepoint(pos):
						if self.engine.selected_unit:
							unit_id = self.engine.selected_unit.id
							result = handle_action(self.engine, "found_city", {"unit_id": unit_id})
							self.engine.show_message(result.message)
						logical_click_handled = True

					elif not logical_click_handled and self.engine.ui_next_turn_button and self.engine.ui_next_turn_button.collidepoint(pos):
						result = handle_action(self.engine, "end_turn", {})
						self.engine.show_message(result.message)
						logical_click_handled = True

					if not logical_click_handled:
						for btn in self.engine.ui_purchase_buttons:
							if btn["rect"].collidepoint(pos):
								itype = btn["type"]
								name = btn["name"]
								city_id = self.engine.selected_city.id if self.engine.selected_city else None
								if city_id is not None:
									action_type = "purchase_building" if itype == "building" else "purchase_unit"
									result = handle_action(self.engine, action_type, {
										"city_id": city_id,
										"name": name
									})
									self.engine.show_message(result.message)
								else:
									self.engine.show_message("No city selected.")
								logical_click_handled = True
								break

					if not logical_click_handled:
						for btn in self.engine.ui_production_buttons:
							if btn["rect"].collidepoint(pos):
								project = btn["project"]
								city_id = self.engine.selected_city.id if self.engine.selected_city else None
								if city_id is not None:
									result = handle_action(self.engine, "choose_project", {
										"city_id": city_id,
										"project_name": project.name
									})
									self.engine.show_message(result.message)
								else:
									self.engine.show_message("No city selected.")
								logical_click_handled = True
								break

					if not logical_click_handled:
						for btn in self.engine.ui_pantheon_buttons:
							if btn["rect"].collidepoint(pos):
								pantheon_name = btn["pantheon_name"]
								result = handle_action(self.engine, "choose_pantheon", {"pantheon_name": pantheon_name})
								self.engine.show_message(result.message)
								logical_click_handled = True
								break

					if not logical_click_handled:
						hex_coords = helper.get_hex_at_pixel(pos[0], pos[1])
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

							elif event.button == 3:
								if 0 <= q < constants.GRID_WIDTH and 0 <= r < constants.GRID_HEIGHT:
									tile = self.engine.tiles[q][r]
									if self.engine.selected_unit:
										unit_id = self.engine.selected_unit.id
										action_data = {"unit_id": unit_id, "to": (q, r)}
										result = handle_action(self.engine, "move_unit", action_data)
										self.engine.show_message(result.message)
										#helper.check_city_state_proximity(self.engine, self.engine.current_player)
										
									elif self.engine.selected_city:
										city_id = self.engine.selected_city.id
										action_data = {"city_id": city_id, "tile_coords": (q, r)}
										result = handle_action(self.engine, "purchase_tile", action_data)
										self.engine.show_message(result.message)
								else:
									self.engine.show_message("Clicked outside map bounds.")
						else:
							self.engine.show_message("Invalid tile.")

			self.renderer.render()
			
		pygame.quit()
