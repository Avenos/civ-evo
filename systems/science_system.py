
from utils import helper, BoolResult
from data import dictionary

class ScienceSystem:
	def __init__(self, player):
		tech_list = helper.build_tech_objects(dictionary.TECHS)
		self.techs = {tech.name: tech for tech in tech_list}
		self.current_research = None
		self.overflow = 0
		self._accumulated_science = 0

		agriculture = self.techs.get("Agriculture")
		if agriculture:
			agriculture.unlocked = True
			agriculture.progress = agriculture.get_effective_cost(player)

		self.set_current_research("Pottery")

	def accumulate_science(self, amount):
		self._accumulated_science += amount

	def process_turn_science(self, science_from_cities, player):
		# Add this turn’s science to the overflow pool
		self._accumulated_science += science_from_cities

		if not self.current_research:
			# No tech selected — keep accumulating
			self.overflow += self._accumulated_science
			self._accumulated_science = 0
			return None

		tech = self.techs[self.current_research]
		total = tech.progress + self._accumulated_science + self.overflow
		cost = tech.get_effective_cost(player)

		if total >= cost:
			tech.unlocked = True
			self.overflow = total - cost
			self._accumulated_science = 0
			self.current_research = None
			#perform era check here
			return tech.name
		else:
			tech.progress = total
			self._accumulated_science = 0
			self.overflow = 0
			return None

	def set_current_research(self, tech_name, player=None):
		tech = self.techs.get(tech_name)

		if not tech:
			return BoolResult(False, f"Tech '{tech_name}' not found.")

		if tech.unlocked:
			return BoolResult(False, f"{tech_name} is already unlocked.")

		if not tech.can_research(self.get_unlocked_names()):
			return BoolResult(False, f"Missing prerequisites for {tech_name}.")

		self.current_research = tech_name

		#why is this here?
		if player and self.overflow > 0:
			tech.progress += self.overflow
			if tech.progress >= tech.get_effective_cost(player):
				tech.unlocked = True
				self.overflow = tech.progress - tech.get_effective_cost(player)
				self.current_research = None
				return BoolResult(True, "Tech unlocked")
			self.overflow = 0  # Apply overflow only once

		return BoolResult(True, f"Selected tech: {tech_name}")
	
	@property
	def current_research_progress(self):
		if self.current_research is None:
			return 0
		else:
			tech = self.techs[self.current_research]
			return tech.progress

	@property
	def unlocked_techs(self):
		return {name for name, tech in self.techs.items() if tech.unlocked}

	#should we return a list of objects not names?
	def get_unlocked_names(self): #objects or names?
		return [name for name, tech in self.techs.items() if tech.unlocked]	

	def get_available_techs(self):
		available = []
		for name, tech in self.techs.items():
			if tech.unlocked:
				continue
			if all(self.techs[req].unlocked for req in tech.prerequisites):
				available.append(name)
		return available
	