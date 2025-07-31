
import pygame
from data import constants

class RenderUI():
	def __init__(self, renderer):
		self.renderer = renderer
		self.engine = renderer.engine
		
	def draw_ui(self):
		bar_height = 30
		bar_bg_color = (220, 220, 220)
		padding = 10
		icon_size = 20
		screen_width = self.renderer.screen.get_width()
		x_offset = 270  # shift everything right
	
		# Background bar (full width, so no x_offset here)
		pygame.draw.rect(self.renderer.base_surface, bar_bg_color, (0, 0, constants.WIDTH, bar_height))
	
		player = self.engine.current_player
		resources = [
			("science", f"+{player.science_per_turn}"),
			("gold", f"{player.gold} +{player.gold_per_turn}"), #negative display?
			("happiness", f"{player.happiness} {player.happiness_points}/{player.happiness_points_needed_for_golden_age}"),
			("culture", f"{player.culture}/{player.policy_cost} +{player.culture_per_turn}"),
			("faith", f"{player.faith} +{player.faith_per_turn}"),
		]
	
		if player.in_golden_age:
			resources.append(("golden_age", f"In golden age! ({player.golden_age_turns_left} turns)"))
	
		x = padding
		y = bar_height // 2
	
		for res_name, res_text in resources:
			icon = self.renderer.icon_images.get(res_name)
			if icon:
				icon_rect = icon.get_rect(midleft=(x + icon_size // 2, y))
				self.renderer.base_surface.blit(icon, icon_rect)
				x += icon_size
				
				if res_name == "happiness" and player.happiness < 0:
					unhappiness_icon = resource_icons.get("unhappiness")
					if unhappiness_icon:
						unhappy_rect = unhappiness_icon.get_rect(midleft=(x + 10, y))
						self.renderer.base_surface.blit(unhappiness_icon, unhappy_rect)
						x += icon_size + 10
	
				x += 20
	
			text_surf = self.renderer.font.render(res_text, True, constants.BLACK)
			text_rect = text_surf.get_rect(midleft=(x, y))
			self.renderer.base_surface.blit(text_surf, text_rect)
			x += text_rect.width
	
			x += padding
	
		col1_x = 1000 + x_offset
		y_offset = bar_height + 10
	
		# Turn counter
		turn_txt = self.renderer.big_font.render(f"Turn: {self.engine.turn}", True, constants.BLACK)
		self.renderer.base_surface.blit(turn_txt, (col1_x, y_offset))
		y_offset += 40
	
		if player.in_golden_age:
			hap_txt = self.renderer.font.render(f"In golden age! ({player.golden_age_turns_left} turns)", True, constants.BLACK)
			self.renderer.base_surface.blit(hap_txt, (col1_x, y_offset))
			y_offset += 40
	
		# Found city button
		if self.engine.selected_unit and self.engine.selected_unit.name == "Settler":
			found_rect = pygame.Rect(col1_x, 450, 120, 40)
			pygame.draw.rect(self.renderer.base_surface, constants.BLACK, found_rect)
			found_txt = self.renderer.big_font.render("Found City", True, constants.WHITE)
			self.renderer.base_surface.blit(found_txt, (found_rect.x + 10, found_rect.y + 10))
			self.engine.ui_found_city_button = found_rect

		# City info panel
		if self.engine.selected_city:
			city = self.engine.selected_city
			info_y = 250
			self.renderer.base_surface.blit(self.renderer.big_font.render("City Info", True, constants.BLACK), (col1_x, info_y))
			city_lines = [
				f"Population: {city.population}",
				f"Food: {city.food} / {city.food_needed_for_growth}",
				f"Food/Turn: {city.food_per_turn}",
				f"Production/Turn: {city.production_per_turn}",
			]
			for i, line in enumerate(city_lines):
				self.renderer.base_surface.blit(self.renderer.font.render(line, True, constants.BLACK), (col1_x, info_y + 30 + i * 30))
	
		# Next Turn button
		next_turn_rect = pygame.Rect(col1_x, 500, 120, 40)
		pygame.draw.rect(self.renderer.base_surface, constants.BLACK, next_turn_rect)
		txt = self.renderer.big_font.render("Next Turn", True, constants.WHITE)
		self.renderer.base_surface.blit(txt, (next_turn_rect.x + 15, next_turn_rect.y + 10))
		self.engine.ui_next_turn_button = next_turn_rect

		# Worker tile improvement buttons
		self.engine.ui_tile_improvement_buttons = []
		if self.engine.selected_unit and self.engine.selected_unit.name == "Worker":
			worker_actions = [
				{"label": "Build Farm", "improvement": "Farm"},
				{"label": "Build Mine", "improvement": "Mine"},
				{"label": "Build Road", "improvement": "Road"},
				{"label": "Remove Forest", "improvement": "Remove Forest"},
			]
			action_y = next_turn_rect.bottom + 10
			action_height = 30
			action_width = 120
			for action in worker_actions:
				action_rect = pygame.Rect(col1_x, action_y, action_width, action_height)
				pygame.draw.rect(self.renderer.base_surface, constants.GRAY, action_rect)
				txt = self.renderer.font.render(action["label"], True, constants.BLACK)
				self.renderer.base_surface.blit(txt, (action_rect.x + 5, action_rect.y + 5))
				self.engine.ui_tile_improvement_buttons.append({
					"rect": action_rect,
					"improvement": action["improvement"]
				})
				action_y += action_height + 5
	
		# --- COLUMN 2: TECH PANEL ---
		col2_x = 1130 + x_offset
		tech_y = 20
		col2_height = 1000
		panel_width = 180
	
		pygame.draw.rect(self.renderer.base_surface, constants.LIGHT_GRAY, (col2_x, tech_y, panel_width, col2_height))
		self.renderer.base_surface.blit(self.renderer.big_font.render("Tech Research", True, constants.BLACK), (col2_x + 10, tech_y + 5))
	
		button_height = 20
		spacing = 5
		start_y = tech_y + 35
		current_research = player.science_system.current_research
	
		self.engine.ui_tech_buttons = []  # ← NEW: Reset list
	
		for i, tech in enumerate(player.science_system.techs.values()):
			y = start_y + i * (button_height + spacing)
			tech_name = tech.name
			cost = tech.get_effective_cost(player)
			progress = cost if tech.unlocked else min(tech.progress, cost)
			unlocked = tech.unlocked
	
			btn_color = constants.GREEN if tech_name == current_research else constants.GRAY
			pygame.draw.rect(self.renderer.base_surface, btn_color, (col2_x + 10, y, panel_width - 20, button_height))
	
			self.renderer.base_surface.blit(self.renderer.font.render(tech_name, True, constants.BLACK), (col2_x + 15, y + 2))
			self.renderer.base_surface.blit(self.renderer.font.render(f"{progress}/{cost}", True, constants.BLACK), (col2_x + panel_width - 60, y + 2))
	
			if unlocked:
				self.renderer.base_surface.blit(self.renderer.font.render("✓", True, constants.BLUE), (col2_x + panel_width - 25, y + 2))
	
			self.engine.ui_tech_buttons.append({
				"rect": pygame.Rect(col2_x + 10, y, panel_width - 20, button_height),
				"tech_name": tech_name,
				"tech": tech
			})
	
		# --- COLUMN 3: CULTURE PANEL ---
		col3_x = 1320 + x_offset
		policy_y = 20
		policy_width = 180
		policy_height = 570
	
		pygame.draw.rect(self.renderer.base_surface, constants.LIGHT_GRAY, (col3_x, policy_y, policy_width, policy_height))
		self.renderer.base_surface.blit(self.renderer.big_font.render("Social Policies", True, constants.BLACK), (col3_x + 10, policy_y + 5))
	
		start_y = policy_y + 35
		button_height = 25
		spacing = 5
	
		self.engine.ui_policy_buttons = []
	
		for i, policy in enumerate(self.engine.all_policies):
			y = start_y + i * (button_height + spacing)
			is_unlocked = policy in player.unlocked_policies
			can_afford = player.culture >= player.policy_cost
	
			if is_unlocked:
				color = (100, 200, 100)
			elif can_afford:
				color = (200, 200, 100)
			else:
				color = (180, 180, 180)
	
			pygame.draw.rect(self.renderer.base_surface, color, (col3_x + 10, y, policy_width - 20, button_height))
			self.renderer.base_surface.blit(self.renderer.font.render(policy, True, constants.BLACK), (col3_x + 15, y + 4))
	
			if is_unlocked:
				self.renderer.base_surface.blit(self.renderer.font.render("Y", True, constants.BLUE), (col3_x + policy_width - 30, y + 4))
	
			self.engine.ui_policy_buttons.append({
				"rect": pygame.Rect(col3_x + 10, y, policy_width - 20, button_height),
				"policy": policy,
				"is_unlocked": is_unlocked,
				"can_afford": can_afford
			})
	
		from entities import Building
	
		# --- COLUMN 4: PURCHASE PANEL ---
		if self.engine.selected_city:
			city = self.engine.selected_city
	
			col4_x = 1510 + x_offset
			col4_y = 20
			col4_width = 180
			col4_height = 600
			line_height = 30
			max_items_visible = col4_height // line_height
	
			pygame.draw.rect(self.renderer.base_surface, constants.LIGHT_GRAY, (col4_x, col4_y, col4_width, col4_height))
			self.renderer.base_surface.blit(self.renderer.big_font.render("Buy Units / Buildings", True, constants.BLACK), (col4_x + 10, col4_y + 5))
	
			purchasables = []
			#for b_name, b_data in dictionary.BUILDINGS.items():
				#if self.engine.selected_city.can_purchase_building(b_name, self.engine.current_player):
					#purchasables.append(("building", b_name, d_data(gold_cost)))
	
			#for u_name, u_data in dictionary.UNITS.items():
				#if self.engine.selected_city.can_purchase_unit(u_name, self.engine.current_player):
					#purchasables.append(("unit", u_name, unit.gold_cost))
					
			# Draw buttons with scrolling if needed (optional)
			self.engine.ui_purchase_buttons = []
			start_y = col4_y + 35
			for i, (itype, name, cost) in enumerate(purchasables[:max_items_visible]):
				btn_rect = pygame.Rect(col4_x + 10, start_y + i * line_height, col4_width - 20, line_height - 6)
	
				# Check if building and already purchased
				if itype == "building" and any(b.name == name for b in city.buildings):
					color = (100, 220, 100)  # light green
				else:
					color = (180, 180, 180)  # default gray
	
				pygame.draw.rect(self.renderer.base_surface, color, btn_rect)
				text = self.renderer.font.render(f"{name} - {cost}g", True, constants.BLACK)
				self.renderer.base_surface.blit(text, (btn_rect.x + 5, btn_rect.y + 5))
	
				self.engine.ui_purchase_buttons.append({
					"rect": btn_rect,
					"type": itype,
					"name": name,
					"cost": cost
				})
	
			# --- Fifth column: Production Projects ---
			city = self.engine.selected_city
	
			col5_x = 1700 + x_offset
			col5_y = 20
			col5_width = 180
			col5_height = 600
			line_height = 30
			max_items_visible = col5_height // line_height
	
			pygame.draw.rect(self.renderer.base_surface, constants.LIGHT_GRAY, (col5_x, col5_y, col5_width, col5_height))
			self.renderer.base_surface.blit(self.renderer.big_font.render("Production Projects", True, constants.BLACK), (col5_x + 10, col5_y + 5))
	
			available_projects = city.production_system.get_available_projects()
			current_project = city.production_system.current_project
	
			start_y = col5_y + 35
			self.engine.ui_production_buttons = []
	
			for i, project in enumerate(available_projects[:max_items_visible]):
				name = project.name
				cost = project.production_cost
				proj_type = project.type
	
				btn_rect = pygame.Rect(col5_x + 10, start_y + i * line_height, col5_width - 20, line_height - 6)
	
				# Determine if this is the current project
				is_current = (
					current_project
					and ((isinstance(current_project, dict) and current_project["name"] == name)
					     or (not isinstance(current_project, dict) and current_project.name == name))
				)
	
				# Highlight color
				color = (100, 220, 100) if is_current else (180, 180, 180)
				pygame.draw.rect(self.renderer.base_surface, color, btn_rect)
	
				# Label: add icon or tag if desired
				display_name = name
	
				self.renderer.base_surface.blit(self.renderer.font.render(f"{display_name} - {cost} prod", True, constants.BLACK), (btn_rect.x + 5, btn_rect.y + 4))
	
				# Show progress if currently building this project
				if is_current:
					if isinstance(current_project, dict):
						progress = current_project.get("progress", 0)
					else:
						progress = current_project.progress
					progress_text = f"Progress: {progress}/{cost}"
					self.renderer.base_surface.blit(self.renderer.font.render(progress_text, True, constants.BLACK), (btn_rect.x + 5, btn_rect.y + 18))
	
				self.engine.ui_production_buttons.append({
					"rect": btn_rect,
					"type": proj_type,
					"name": name,
					"cost": cost,
					"project": project,
				})
	
		# --- COLUMN 6: PANTHEON SELECTION ---
		self.engine.ui_pantheon_buttons = []
		if self.engine.current_player.pantheon is None:
			required_faith = 20 + (self.engine.turn // 10) * 5
			if self.engine.current_player.faith >= required_faith:
				col6_x = 2130 + x_offset  # shifted right by 100
				col6_y = 20
				col6_width = 240
				col6_height = 500
				line_height = 30
				max_items_visible = col6_height // line_height
	
				pygame.draw.rect(self.renderer.base_surface, (220, 220, 200), (col6_x, col6_y, col6_width, col6_height))
				self.renderer.base_surface.blit(self.renderer.big_font.render("Choose a Pantheon", True, constants.BLACK), (col6_x + 10, col6_y + 5))
	
				start_y = col6_y + 35
				pantheons_list = list(self.engine.all_pantheons.items())
				for i, (name, data) in enumerate(pantheons_list[:max_items_visible]):
					effect = data.get("desc", "")
					rect = pygame.Rect(col6_x + 10, start_y + i * line_height, col6_width - 20, line_height - 6)
	
					pygame.draw.rect(self.renderer.base_surface, (180, 180, 180), rect)
					self.renderer.base_surface.blit(self.renderer.font.render(name, True, constants.BLACK), (rect.x + 5, rect.y + 4))
	
					self.engine.ui_pantheon_buttons.append({
						"rect": rect,
						"pantheon_name": name,
						"pantheon_data": data
					})
