
import random
import pygame
import time
import helper
import renderer
from dictionary import TERRAIN_TYPES
from action_handler import handle_action, start_new_log
from engine import Engine
from constants import GRID_WIDTH, GRID_HEIGHT, HEX_RADIUS, WIDTH, HEIGHT, FPS, CITY_NAMES

def run_random_agent(engine, headless=False):
	screen, clock, font, big_font, terrain_overlays, resource_icons, unit_icons = helper.init_pygame_assets(headless=headless)

	start_new_log(engine)
	BASE_WIDTH = WIDTH
	BASE_HEIGHT = HEIGHT
	running = True

	while running:
		clock.tick(FPS)

		if not headless:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False

		if engine.message_timer > 0:
			engine.message_timer -= 1

		legal_actions = engine.get_legal_actions(engine.current_player)
		if not legal_actions:
			break  # Safety guard

		action = random.choice(legal_actions)
		handle_action(engine, action["action"], action["data"])

		if headless:
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
		hex_mask = helper.create_hex_mask(HEX_RADIUS)
		renderer.draw_grid(base_surface, engine, font, big_font, terrain_overlays, hex_mask, resource_icons)
		renderer.draw_territory_shading(base_surface, engine, font, big_font)
		renderer.draw_cities(base_surface, engine, font, big_font)
		renderer.draw_units(base_surface, engine, font, big_font, unit_icons)
		renderer.draw_ui(base_surface, engine, font, big_font, resource_icons)
		renderer.draw_message(base_surface, engine)

		scaled_surface = pygame.transform.smoothscale(base_surface, (scaled_width, scaled_height))
		screen.fill((0, 0, 0))
		screen.blit(scaled_surface, (x_offset, y_offset))

		pygame.display.flip()
		pygame.time.wait(50)

	if not headless:
		pygame.quit()
