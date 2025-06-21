
import random
import json

#turn 121 to beat:
#science +195, 6 turns till banking
#crop yield 200, 10 cities total
#86 hammers
#27 culture per turn
#900 + 97 gold per turn


class EvolutionarySimulator:
	def __init__(self, num_generations=100, population_size=50):
		self.num_generations = num_generations
		self.population_size = population_size
		self.population = []  # list of AI agents
		self.history = []     # log of events/actions

	def initialize_population(self):
		self.population = [self.create_random_agent() for _ in range(self.population_size)]

	def create_random_agent(self):
		# This can be a random policy or neural net or rule set
		return {
	        "parameters": {
	            "aggressiveness": random.uniform(0, 1),
	        "expansion_rate": random.uniform(0, 1),
	        "build_order": [random.choice(["Worker", "Scout", "Settler"]) for _ in range(5)]
	        },
	    "fitness": 0
	}

	def evaluate(self, agent):
		# TODO: Plug into your game simulation
		# Run the game with this agent and record actions
		sim = SingleGameSimulator(agent, record=True)
		agent["fitness"], recorded_actions = sim.run()
		self.history.append(recorded_actions)

	def run(self):
		self.initialize_population()
		for gen in range(self.num_generations):
			print(f"Generation {gen + 1}")
			for agent in self.population:
				self.evaluate(agent)

			# Select top agents
			self.population.sort(key=lambda a: a["fitness"], reverse=True)
			top = self.population[:self.population_size // 2]

			# Reproduce
			self.population = top + self.mutate(top)

		# Save best history
		self.save_replay(self.history[-1], "replay_final.json")

	def mutate(self, agents):
		children = []
		for agent in agents:
			child = {
	            "parameters": {
	                key: max(0, min(1, val + random.uniform(-0.1, 0.1))) if isinstance(val, float) else val
	            for key, val in agent["parameters"].items()
	            },
	        "fitness": 0
	    }
			children.append(child)
		return children

	def save_replay(self, action_log, filename):
		with open(filename, "w") as f:
			json.dump(action_log, f)

class SingleGameSimulator:
	def __init__(self, agent, record=False):
		self.agent = agent
		self.record = record
		self.recorded_actions = []

		# Initialize game engine with seed, etc.
		self.engine = create_game_with_ai_agent(agent)

	def run(self):
		turns = 60  # Or until victory
		for _ in range(turns):
			actions = self.engine.ai_take_turn()
			if self.record:
				self.recorded_actions.append(actions)

		return self.engine.evaluate_result(), self.recorded_actions
