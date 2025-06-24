
import game_loop
import evolution
import replay
import pygame
from engine import Engine

def main():
	pygame.init()
	
	#pygame.mixer.init()
	#try:
		#pygame.mixer.music.load("assets\\music\\gandhiX.mp3")
		#pygame.mixer.music.play(-1)  # -1 means loop indefinitely
	#except Exception as e:
		#print(f"Music failed to load: {e}")

	engine = Engine()

	# Uncomment to generate and save a random map
	# tiles = map_generator.generate_random_map(23, 23)
	# map_generator.save_map_to_json(tiles, "randomMap.json", 23, 23)

	# Uncomment to replay
	#replay.play_replay("replay_2025-06-22_21-36-40.json", engine, speed=1.0)

	game_loop.run_manual_game(engine)

if __name__ == "__main__":
	main()
