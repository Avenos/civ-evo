
import math
import pygame
import helper
import dictionary
import os
import numpy as np
from constants import GRID_WIDTH, GRID_HEIGHT, HEX_RADIUS, WIDTH, HEIGHT, FPS, HEX_DIAMETER, HEX_RADIUS

WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
CYAN = (0, 180, 200)
YELLOW = (255, 255, 0)

def blit_hex_overlay_clipped(screen, overlay_img, center_x, center_y, mask_surf):
	# 1. Scale overlay_img to hex diameter
	overlay_scaled = pygame.transform.smoothscale(overlay_img, (HEX_DIAMETER, HEX_DIAMETER))

	# 2. Create a temporary surface with per-pixel alpha
	temp_surf = pygame.Surface((HEX_DIAMETER, HEX_DIAMETER), pygame.SRCALPHA)

	# 3. Blit overlay onto temp surface
	temp_surf.blit(overlay_scaled, (0, 0))

	# 4. Use mask_surf alpha channel to clip pixels outside hex
	overlay_alpha = pygame.surfarray.pixels_alpha(temp_surf)
	mask_alpha = pygame.surfarray.pixels_alpha(mask_surf)

	# Multiply alpha channels pixel-wise, converting mask_alpha to float 0-1
	overlay_alpha[:] = (overlay_alpha * (mask_alpha / 255.0)).astype(np.uint8)

	# 5. Delete surfarray references to unlock surfaces
	del overlay_alpha, mask_alpha

	# 6. Calculate top-left to blit since center_x, center_y is center coords
	top_left_x = center_x - HEX_RADIUS
	top_left_y = center_y - HEX_RADIUS

	# 7. Blit the masked surface onto screen
	screen.blit(temp_surf, (top_left_x, top_left_y))

def draw_hex(surface, x, y, color, width=2):
	points = []
	for i in range(6):
		angle = math.radians(60 * i - 30)  # shift by -30 degrees for pointy-top
		px = x + HEX_RADIUS * math.cos(angle)
		py = y + HEX_RADIUS * math.sin(angle)
		points.append((px, py))
	pygame.draw.polygon(surface, color, points, width)

def draw_grid(screen, engine, font, big_font, terrain_overlays, hex_mask, icon_images):
	for q in range(GRID_WIDTH):
		for r in range(GRID_HEIGHT):
			x, y = helper.hex_to_pixel(q, r)
			tile = engine.tiles[q][r]  # columns then rows

			key = helper.build_tile_image_key(tile, terrain_overlays.keys())
			img = terrain_overlays.get(key)

			if img:
				blit_hex_overlay_clipped(screen, img, x, y, hex_mask)
			else:
				base_img = terrain_overlays.get(tile.terrain_type.lower())
				if base_img:
					blit_hex_overlay_clipped(screen, base_img, x, y, hex_mask)
				else:
					points = [helper.get_hex_corner(x, y, i) for i in range(6)]
					pygame.draw.polygon(screen, BLACK, points)

			# Draw ancient ruin
			if tile.ancient_ruin:
				ar_text = "AR"
				ar_surf = font.render(ar_text, True, (139, 69, 19))
				ar_rect = ar_surf.get_rect(center=(x, y + HEX_RADIUS // 2))
				screen.blit(ar_surf, ar_rect)

				# --- Draw tile yield icons ---
				yield_offset_x = -20  # Adjust horizontal spacing between icons
				yield_offset_y = HEX_RADIUS // 3  # Slightly below center of tile

			icon_spacing = 16
			yield_offset_x = -10
			yield_offset_y = HEX_RADIUS // 3
			current_x = x + yield_offset_x

			for attr in ["food", "production", "gold", "science", "culture", "faith"]:
				amount = getattr(tile, attr, 0)
				if amount > 0:
					icon = icon_images.get(attr)
					if icon:
						for _ in range(amount):
							icon_rect = icon.get_rect(midbottom=(current_x, y + yield_offset_y))
							screen.blit(icon, icon_rect)
							current_x += icon_spacing

						# Draw hex border
						draw_hex(screen, x, y, BLACK)

						# Draw rivers
						for edge_index in tile.rivers:
							start = helper.get_hex_corner(x, y, edge_index)
							end = helper.get_hex_corner(x, y, (edge_index + 1) % 6)
							pygame.draw.line(screen, CYAN, start, end, 5)						

def draw_territory_shading(screen, engine, font, big_font):
	territory_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

	for row in engine.tiles:
		for tile in row:
			if tile.owner:
				player_index = engine.players.index(tile.owner)
				color = dictionary.PLAYER_COLORS[player_index % len(dictionary.PLAYER_COLORS)]

				x, y = helper.hex_to_pixel(tile.q, tile.r)
				points = []
				for i in range(6):
					angle = math.radians(60 * i - 30)
					px = x + HEX_RADIUS * math.cos(angle)
					py = y + HEX_RADIUS * math.sin(angle)
					points.append((px, py))
				pygame.draw.polygon(territory_surf, color, points)

	screen.blit(territory_surf, (0, 0))

def draw_cities(screen, engine, font, big_font):
	GOLD_DARK_GREEN = (34, 139, 34)
	DARK_YELLOW = (204, 153, 0)

	for player in engine.players:
		for city in player.cities:
			x, y = helper.hex_to_pixel(city.q, city.r)

			# Draw city population number
			label = big_font.render(str(city.population), True, GOLD_DARK_GREEN)
			label_rect = label.get_rect(center=(x, y))
			screen.blit(label, label_rect)

			# Only draw worked tile dots if this city is selected
			if engine.selected_city == city:
				for tile in city.worked_tiles:
					if (tile.q, tile.r) == (city.q, city.r):
						continue  # skip city tile itself
					wx, wy = helper.hex_to_pixel(tile.q, tile.r)
					pygame.draw.circle(screen, DARK_YELLOW, (int(wx), int(wy)), 6)

def draw_units(screen, engine, font, big_font, unit_icons):
	ICON_SIZE = 40  # or smaller, e.g., 16

	for unit in engine.players[0].units:
		x, y = helper.hex_to_pixel(unit.q, unit.r)
		selected = (unit == engine.selected_unit)

		if selected:
			draw_hex(screen, x, y, GREEN, width=3)

		icon = unit_icons.get(unit.name.lower())  # or however you key them
		if icon:
			scaled_icon = pygame.transform.smoothscale(icon, (ICON_SIZE, ICON_SIZE))
			icon_rect = scaled_icon.get_rect(center=(x, y))
			screen.blit(scaled_icon, icon_rect)
		else:
			# fallback to text label if icon missing
			color = GREEN if selected else BLUE
			label = big_font.render(unit.name, True, color)
			label_rect = label.get_rect(center=(x, y))
			screen.blit(label, label_rect)

def draw_message(screen, engine):
	if engine.message_timer > 0 and engine.message:
		font = pygame.font.SysFont("arial", 18)
		text_surface = font.render(engine.message, True, (255, 255, 255))
		background = pygame.Surface((text_surface.get_width() + 20, text_surface.get_height() + 10))
		background.set_alpha(180)
		background.fill(BLACK)
		screen.blit(background, (10, 10))
		screen.blit(text_surface, (20, 15))

def draw_ui(screen, engine, font, big_font, resource_icons):
	bar_height = 30
	bar_bg_color = (220, 220, 220)
	padding = 10
	icon_size = 20
	screen_width = screen.get_width()
	x_offset = 200  # shift everything right by 100 px

	# Background bar (full width, so no x_offset here)
	pygame.draw.rect(screen, bar_bg_color, (0, 0, screen_width, bar_height))

	player = engine.current_player
	resources = [
		("science", f"+{player.science_per_turn}"),
		("gold", f"{player.gold} +{player.gold_per_turn}"),
		("happiness", f"{player.happiness} {player.happiness_points}/{player.happiness_points_needed_for_golden_age}"),
		("culture", f"{player.culture}/{player.policy_cost} +{player.culture_per_turn}"),
		("faith", f"{player.faith} +{player.faith_per_turn}"),
	]

	if player.in_golden_age:
		resources.append(("golden_age", f"In golden age! ({player.golden_age_turns_left} turns)"))

	x = padding + x_offset
	y = bar_height // 2

	for res_name, res_text in resources:
		icon = resource_icons.get(res_name)
		if icon:
			icon_rect = icon.get_rect(midleft=(x + icon_size // 2, y))
			screen.blit(icon, icon_rect)
			x += icon_size  # move right past icon

			# Special: Show unhappiness icon right after happiness icon & text if happiness < 0
			if res_name == "happiness" and player.happiness < 0:
				unhappiness_icon = resource_icons.get("unhappiness")
				if unhappiness_icon:
					unhappy_rect = unhappiness_icon.get_rect(midleft=(x + 10, y))  # 10 px gap after happiness icon
					screen.blit(unhappiness_icon, unhappy_rect)
					x += icon_size + 10  # move past unhappy icon + spacing

			x += 20  # bigger gap between icon and text

		text_surf = font.render(res_text, True, BLACK)
		text_rect = text_surf.get_rect(midleft=(x, y))
		screen.blit(text_surf, text_rect)
		x += text_rect.width

		x += padding  # normal small gap before next icon

	col1_x = 1000 + x_offset
	y_offset = bar_height + 10

	# Turn counter (moved down)
	turn_txt = big_font.render(f"Turn: {engine.turn}", True, BLACK)
	screen.blit(turn_txt, (col1_x, y_offset))
	y_offset += 40

	if player.in_golden_age:
		hap_txt = font.render(f"In golden age! ({player.golden_age_turns_left} turns)", True, BLACK)
		screen.blit(hap_txt, (col1_x, y_offset))
		y_offset += 40

	# found city button
	if engine.selected_unit and engine.selected_unit.name == "Settler":
		found_rect = pygame.Rect(col1_x, 450, 120, 40)
		pygame.draw.rect(screen, BLACK, found_rect)
		found_txt = big_font.render("Found City", True, WHITE)
		screen.blit(found_txt, (found_rect.x + 10, found_rect.y + 10))
		engine.ui_found_city_button = found_rect

	# City info panel
	if engine.selected_city:
		city = engine.selected_city
		info_y = 250
		screen.blit(big_font.render("City Info", True, BLACK), (col1_x, info_y))
		city_lines = [
			f"Population: {city.population}",
			f"Food: {city.food} / {city.food_needed_for_growth}",
			f"Food/Turn: {city.food_per_turn}",
			f"Production/Turn: {city.production_per_turn}",
		]
		for i, line in enumerate(city_lines):
			screen.blit(font.render(line, True, BLACK), (col1_x, info_y + 30 + i * 30))

	# Next Turn button
	next_turn_rect = pygame.Rect(col1_x, 500, 120, 40)
	pygame.draw.rect(screen, BLACK, next_turn_rect)
	txt = big_font.render("Next Turn", True, WHITE)
	screen.blit(txt, (next_turn_rect.x + 15, next_turn_rect.y + 10))
	engine.ui_next_turn_button = next_turn_rect

	# --- COLUMN 2: TECH PANEL ---
	col2_x = 1170 + x_offset
	tech_y = 20
	panel_width = 180

	pygame.draw.rect(screen, (220, 220, 220), (col2_x, tech_y, panel_width, 500))
	screen.blit(big_font.render("Tech Research", True, BLACK), (col2_x + 10, tech_y + 5))

	button_height = 20
	spacing = 5
	start_y = tech_y + 35
	current_research = player.science_system.current_research

	engine.ui_tech_buttons = []  # ← NEW: Reset list

	for i, tech in enumerate(player.science_system.techs.values()):
		y = start_y + i * (button_height + spacing)
		tech_name = tech.name
		cost = tech.get_effective_cost(player)
		progress = cost if tech.unlocked else min(tech.progress, cost)
		unlocked = tech.unlocked

		btn_color = GREEN if tech_name == current_research else GRAY
		pygame.draw.rect(screen, btn_color, (col2_x + 10, y, panel_width - 20, button_height))

		screen.blit(font.render(tech_name, True, BLACK), (col2_x + 15, y + 2))
		screen.blit(font.render(f"{progress}/{cost}", True, BLACK), (col2_x + panel_width - 60, y + 2))

		if unlocked:
			screen.blit(font.render("✓", True, BLUE), (col2_x + panel_width - 25, y + 2))

		engine.ui_tech_buttons.append({
			"rect": pygame.Rect(col2_x + 10, y, panel_width - 20, button_height),
			"tech_name": tech_name,
			"tech": tech
		})

	# --- COLUMN 3: CULTURE PANEL ---
	col3_x = 1370 + x_offset
	policy_y = 20
	policy_width = 200
	policy_height = 500

	pygame.draw.rect(screen, (230, 230, 230), (col3_x, policy_y, policy_width, policy_height))
	screen.blit(big_font.render("Social Policies", True, BLACK), (col3_x + 10, policy_y + 5))

	start_y = policy_y + 35
	button_height = 25
	spacing = 5

	engine.ui_policy_buttons = []

	for i, policy in enumerate(engine.all_policies):
		y = start_y + i * (button_height + spacing)
		is_unlocked = policy in player.unlocked_policies
		can_afford = player.culture >= player.policy_cost

		if is_unlocked:
			color = (100, 200, 100)
		elif can_afford:
			color = (200, 200, 100)
		else:
			color = (180, 180, 180)

		pygame.draw.rect(screen, color, (col3_x + 10, y, policy_width - 20, button_height))
		screen.blit(font.render(policy, True, BLACK), (col3_x + 15, y + 4))

		if is_unlocked:
			screen.blit(font.render("✓", True, BLUE), (col3_x + policy_width - 30, y + 4))

		engine.ui_policy_buttons.append({
			"rect": pygame.Rect(col3_x + 10, y, policy_width - 20, button_height),
			"policy": policy,
			"is_unlocked": is_unlocked,
			"can_afford": can_afford
		})

	from core import Building

	# --- COLUMN 4: PURCHASE PANEL ---
	if engine.selected_city:
		city = engine.selected_city

		col4_x = 1610 + x_offset  # shifted right by 100
		col4_y = 20
		col4_width = 220
		col4_height = 500
		line_height = 30
		max_items_visible = col4_height // line_height

		pygame.draw.rect(screen, (210, 210, 210), (col4_x, col4_y, col4_width, col4_height))
		screen.blit(big_font.render("Buy Units / Buildings", True, BLACK), (col4_x + 10, col4_y + 5))

		# Build purchasables list (filter if needed)
		purchasables = []
		for b_name, b_data in dictionary.BUILDINGS.items():
			building = Building(b_name, **b_data)
			purchasables.append(("building", b_name, building.gold_cost))

		for u_name, unit in dictionary.UNITS.items():
			purchasables.append(("unit", u_name, unit.get("gold_cost", 0)))

		# Draw buttons with scrolling if needed (optional)
		engine.ui_purchase_buttons = []
		start_y = col4_y + 35
		for i, (itype, name, cost) in enumerate(purchasables[:max_items_visible]):
			btn_rect = pygame.Rect(col4_x + 10, start_y + i * line_height, col4_width - 20, line_height - 6)

			# Check if building and already purchased
			if itype == "building" and any(b.name == name for b in city.buildings):
				color = (100, 220, 100)  # light green
			else:
				color = (180, 180, 180)  # default gray

			pygame.draw.rect(screen, color, btn_rect)
			text = font.render(f"{name} - {cost}g", True, BLACK)
			screen.blit(text, (btn_rect.x + 5, btn_rect.y + 5))

			engine.ui_purchase_buttons.append({
				"rect": btn_rect,
				"type": itype,
				"name": name,
				"cost": cost
			})

		# --- Fifth column: Production Projects ---
		city = engine.selected_city

		col5_x = 1860 + x_offset  # shifted right by 100
		col5_y = 20
		col5_width = 220
		col5_height = 500
		line_height = 30
		max_items_visible = col5_height // line_height

		pygame.draw.rect(screen, (200, 200, 200), (col5_x, col5_y, col5_width, col5_height))
		screen.blit(big_font.render("Production Projects", True, BLACK), (col5_x + 10, col5_y + 5))

		available_projects = city.production_system.get_available_projects()
		current_project = city.production_system.current_project

		start_y = col5_y + 35
		engine.ui_production_buttons = []

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
			pygame.draw.rect(screen, color, btn_rect)

			# Label: add icon or tag if desired
			display_name = name

			screen.blit(font.render(f"{display_name} - {cost} prod", True, BLACK), (btn_rect.x + 5, btn_rect.y + 4))

			# Show progress if currently building this project
			if is_current:
				if isinstance(current_project, dict):
					progress = current_project.get("progress", 0)
				else:
					progress = current_project.progress
				progress_text = f"Progress: {progress}/{cost}"
				screen.blit(font.render(progress_text, True, BLACK), (btn_rect.x + 5, btn_rect.y + 18))

			engine.ui_production_buttons.append({
				"rect": btn_rect,
				"type": proj_type,
				"name": name,
				"cost": cost,
				"project": project,
			})

	# --- COLUMN 6: PANTHEON SELECTION ---
	engine.ui_pantheon_buttons = []
	if engine.current_player.pantheon is None:
		required_faith = 20 + (engine.turn // 10) * 5
		if engine.current_player.faith >= required_faith:
			col6_x = 2130 + x_offset  # shifted right by 100
			col6_y = 20
			col6_width = 240
			col6_height = 500
			line_height = 30
			max_items_visible = col6_height // line_height

			pygame.draw.rect(screen, (220, 220, 200), (col6_x, col6_y, col6_width, col6_height))
			screen.blit(big_font.render("Choose a Pantheon", True, BLACK), (col6_x + 10, col6_y + 5))

			start_y = col6_y + 35
			pantheons_list = list(engine.all_pantheons.items())
			for i, (name, data) in enumerate(pantheons_list[:max_items_visible]):
				effect = data.get("desc", "")
				rect = pygame.Rect(col6_x + 10, start_y + i * line_height, col6_width - 20, line_height - 6)

				pygame.draw.rect(screen, (180, 180, 180), rect)
				screen.blit(font.render(name, True, BLACK), (rect.x + 5, rect.y + 4))

				engine.ui_pantheon_buttons.append({
					"rect": rect,
					"pantheon_name": name,
					"pantheon_data": data
				})