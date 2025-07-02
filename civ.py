
import pygame
import game_loop
import randomAgent
import replay
from engine import Engine

def main():
	pygame.init()
	
	engine = Engine()
	
	randomAgent.run_random_agent(engine, True)
	#game_loop.run_manual_game(engine)
	#replay.play_replay("replay_2025-06-22_21-36-40.json", engine, speed=1.0)

if __name__ == "__main__":
	main()
