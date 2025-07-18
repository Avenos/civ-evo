
#here is random_agent.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import random
import pygame
import time

from data import dictionary, constants
from engine import Engine, handle_action, start_new_log
from renderer import Renderer
from utils import helper

class RandomAgent:
	def __init__(self, engine, headless=True):
		self.engine = engine
		self.renderer = Renderer(engine)
		self.headless = headless

	def run(self):
		#start_new_log(self.engine)
		
		self.clock = clock = pygame.time.Clock()
		running = True

		while running:
			clock.tick(constants.FPS)

			if not self.headless:
				for event in pygame.event.get():
					if event.type == pygame.QUIT:
						running = False

			if self.engine.message_timer > 0:
				self.engine.message_timer -= 1

			legal_actions = self.engine.get_legal_actions(self.engine.current_player)
			if not legal_actions:
				break  # Safety guard

			action = random.choice(legal_actions)
			handle_action(self.engine, action["action"], action["data"], False)

			if not self.headless:
				self.renderer.render()
			#pygame.time.wait(50)

		if not self.headless:
			pygame.quit()
