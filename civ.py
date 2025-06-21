
import game_loop
import evolution
import map_generator
import replay
import pygame
from engine import Engine

def main():
	#tiles = map_generator.generate_random_map(9, 9)
	#map_generator.save_map_to_json(tiles, "randomMap.json", 9, 9)
	
	engine = Engine()

	#replay.play_replay("replay_2025-06-20_22-11-14.json", engine, speed=1.0)
	game_loop.run_manual_game(engine)

if __name__ == "__main__":
	main()