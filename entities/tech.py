class Tech:
	def __init__(self, name, base_cost, prerequisites=None):
		self.name = name
		self.base_cost = base_cost
		self.prerequisites = prerequisites or []
		self.progress = 0
		self.unlocked = False

	def can_research(self, unlocked_techs):
		return all(prereq in unlocked_techs for prereq in self.prerequisites)

	def get_effective_cost(self, player):
		extra_cities = max(0, len(player.cities) - 1)
		modifier = 1.30 + 0.02 * extra_cities
		return int(self.base_cost * modifier)
