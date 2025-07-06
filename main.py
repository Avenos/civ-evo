
import pygame
from engine import Engine, HumanGame, Replay
from ai import SmartAgent, RandomAgent

def main():
	pygame.init()
	engine = Engine()
	
	#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	#train.train_agent(num_episodes=1000)
	
	#HumanGame(engine).run()
	RandomAgent(engine).run()
	#Replay("replay1.json", engine, speed=1.0).play

if __name__ == "__main__":
	main()
