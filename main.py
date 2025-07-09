
import pygame
from engine import Engine, HumanGame, Replay
from ai import SmartAgent, RandomAgent

def main():
	pygame.init()
	engine = Engine()
	
	#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	#train.train_agent(num_episodes=1000)
	
	HumanGame(engine).run()
	#RandomAgent(engine, True).run()
	#Replay("replay_2025-07-09_05-43-38.json", engine, speed=9999999).run()

if __name__ == "__main__":
	main()
