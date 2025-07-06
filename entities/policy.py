
class Policy:
	def __init__(self, name, era = 'ancient', prerequisites=None, desc=""):
		self.name = name
		self.prerequisites = prerequisites if prerequisites else []
		self.desc = desc
		self.era = era

	def is_unlocked(self, player):
		return self.name in player.unlocked_policies

	#not a huge fan of this
	def can_unlock(self, player):
		return all(prereq in player.unlocked_policies for prereq in self.prerequisites)