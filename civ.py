
import game_loop
import evolution
import replay
import pygame
from engine import Engine
from constants import WIDTH, HEIGHT

def main():
	engine = Engine()
	
	replay.play_replay("replay1.json", engine, speed=1.0)
	#game_loop.run_manual_game(engine)

if __name__ == "__main__":
	main()