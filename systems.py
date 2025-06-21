
import helper
import dictionary

class ProductionSystem:
	def __init__(self, city):
		self.city = city

		#is this available or all or what?
		self.building_projects = [helper.create_building(name, data) for name, data in dictionary.BUILDINGS.items()]
		self.unit_projects = [helper.create_unit(name, data) for name, data in dictionary.UNITS.items()]

		self.projects = self.building_projects + self.unit_projects

		self.current_project = None  # Can be building or unit (store as a dict/object)

	def can_choose_project(self, project):
		from core import Unit
	
		player = self.city.owner
		unlocked_techs = player.science_system.get_unlocked_names()
		unlocked_policies = player.unlocked_policies
	
		project_name = project.name
	
		if project.completed:
			return False, f"Project '{project_name}' is already completed."
	
		if project.production_cost <= 0:
			return False, f"Project '{project_name}' cannot be produced."
	
		missing_tech = next((req for req in project.techs_required if req not in unlocked_techs), None)
		if missing_tech:
			return False, f"Tech requirement '{missing_tech}' not met for '{project_name}'."
	
		missing_policy = next((req for req in project.policies_required if req not in unlocked_policies), None)
		if missing_policy:
			return False, f"Policy requirement '{missing_policy}' not met for '{project_name}'."
	
		# Disallow building Monument if we have a monument (FREE) in the city
		if project_name == "Monument":
			has_monument = any("Monument" in b.name for b in self.city.buildings)
			if has_monument:
				return False, "A Monument is already present in the city."
	
		# Settler restriction
		if isinstance(project, Unit) and project_name == "Settler" and self.city.population < 2:
			return False, "Settler cannot be built unless city population is at least 2."
	
		return True, None
	
	
	def get_available_projects(self):
		seen = set()
		available = []
	
		for proj in self.projects:
			if proj.name in seen:
				continue
	
			success, _ = self.can_choose_project(proj)
			if success:
				available.append(proj)
				seen.add(proj.name)
	
		return available
	
	
	def choose_project(self, project_name):
		from core import Unit
		from helper import create_unit, create_building
		import dictionary
	
		player = self.city.owner
	
		# Always create a fresh instance of the selected project
		if project_name in dictionary.UNITS:
			project_data = dictionary.UNITS[project_name]
			project = create_unit(project_name, project_data)
		elif project_name in dictionary.BUILDINGS:
			project_data = dictionary.BUILDINGS[project_name]
			project = create_building(project_name, project_data)
		else:
			return False, f"Project data for '{project_name}' not found."
	
		# Validate that project can be started now
		success, message = self.can_choose_project(project)
		if not success:
			return False, message
	
		# ✅ Assign freshly created project
		self.current_project = project
		return True, f"Started {project_name}."




	def apply_production(self, engine):
		from core import Unit
		if not self.current_project:
			return

		production = self.city.production_per_turn

		# Check if current project is a Unit or Building based on class
		if isinstance(self.current_project, Unit):
			unit = self.current_project
			unit.progress += production

			if unit.progress >= unit.production_cost:
				self.complete_unit(unit.name, self.city.q, self.city.r, engine)
				self.current_project = None

		else:
			# Assume building
			building = self.current_project
			if building.completed:
				return
			building.progress += production

			if building.progress >= building.production_cost:
				building.completed = True
				building.progress = building.production_cost
				self.complete_building(building.name)
				self.current_project = None

	def get_progress(self, project_name=None):
		if project_name:
			# Look in buildings
			for b in self.building_projects:
				if b.name == project_name:
					return b.progress
			# Look in units
			for u in self.unit_projects:
				if u["name"] == project_name:
					return u.get("progress", 0)
			return 0

		if self.current_project:
			if isinstance(self.current_project, dict):
				return self.current_project.get("progress", 0)
			else:
				return self.current_project.progress
		return 0

	def complete_building(self, building_name):
		for b in self.building_projects:  # ONLY buildings here
			if b.name == building_name:
				b.completed = True
				b.progress = b.production_cost
				self.city.buildings.append(b)
				return
	def complete_unit(self, unit_name, q, r, engine):
		engine.spawn_unit(player=self.city.owner, q=q, r=r, name=unit_name)
		print(f"[DEBUG] Spawned unit '{unit_name}' at city ({self.city.q},{self.city.r}) for player '{self.city.owner.name}'.")

	def is_completed(self, project_name):
		for b in self.building_projects:
			if b.name == project_name:
				return b.completed
		return False  # Units aren't persistent objects in this system

	def get_current_project_name(self):
		if not self.current_project:
			return None
		return self.current_project["name"] if isinstance(self.current_project, dict) else self.current_project.name


class Policy:
	def __init__(self, name, prerequisites=None, desc=""):
		self.name = name
		self.prerequisites = prerequisites if prerequisites else []
		self.desc = desc

	def is_unlocked(self, player):
		return self.name in player.unlocked_policies

	def can_unlock(self, player):
		return all(prereq in player.unlocked_policies for prereq in self.prerequisites)
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
			return tech.name
		else:
			tech.progress = total
			self._accumulated_science = 0
			self.overflow = 0
			return None

	@property
	def unlocked_techs(self):
		return {name for name, tech in self.techs.items() if tech.unlocked}                

	def set_current_research(self, tech_name, player=None):
		tech = self.techs.get(tech_name)
	
		if not tech:
			return False, f"Tech '{tech_name}' not found."
	
		if tech.unlocked:
			return False, f"{tech_name} is already unlocked."
	
		if not tech.can_research(self.get_unlocked_names()):
			return False, f"Missing prerequisites for {tech_name}."
	
		self.current_research = tech_name
	
		if player and self.overflow > 0:
			tech.progress += self.overflow
			if tech.progress >= tech.get_effective_cost(player):
				tech.unlocked = True
				self.overflow = tech.progress - tech.get_effective_cost(player)
				self.current_research = None
				return True, None
			self.overflow = 0  # Apply overflow only once
	
		return True, f"Selected tech: {tech_name}"

	def get_unlocked_names(self):
		return [name for name, tech in self.techs.items() if tech.unlocked]

	def get_next_researchable(self):
		for tech in self.techs.values():
			if not tech.unlocked and tech.can_research(self.get_unlocked_names()):
				return tech.name
		return None

class AncientRuins:
	RINDS_EFFECTS = {
		1: "Gain 75 gold",
		2: "Gain 20 faith", #only possibly triggers AFTER turn 20
		3: "Gain 1 pop in nearest city",
		4: "Reveal nearby tiles (useless)",
		5: "Unit upgrades (useless)",
		6: "Reveal barbarian camps (useless)",
		7: "Free tech",
		8: "Gain 20 culture"
	}

	def __init__(self, effect_id):
		self.effect_id = effect_id
		self.description = self.RINDS_EFFECTS.get(effect_id, "Unknown effect")

	def trigger(self, player, tile):
		if self.effect_id == 1:
			player.gold += 75
		elif self.effect_id == 2:
			player.faith += 20
		elif self.effect_id == 3:
			# Gain 1 pop in nearest city; if tie, choose earliest founded
			if not player.cities:
				return  # no cities to grow
			# Calculate distance from tile to each city
			cities_with_dist = []
			for city in player.cities:
				dist = hex_distance(tile.q, tile.r, city.q, city.r)
				cities_with_dist.append((dist, city))
			cities_with_dist.sort(key=lambda x: x[0])  # sort by distance ascending

			# Get shortest distance
			min_dist = cities_with_dist[0][0]

			# Get all cities tied at min_dist
			closest_cities = [c for d, c in cities_with_dist if d == min_dist]

			# Assuming cities list order is creation order, pick the first in that tie
			city_to_grow = None
			for city in player.cities:
				if city in closest_cities:
					city_to_grow = city
					break

			if city_to_grow:
				city_to_grow.population += 1
				city_to_grow.update_worked_tiles(player.game)  # or however you update city stats

		elif self.effect_id == 4:
			pass
		elif self.effect_id == 5:
			pass
		elif self.effect_id == 6:
			pass
		elif self.effect_id == 7:
			unlocked_techs = player.science_system.get_unlocked_names()
			current_progress = player.science_system.current_research_progress
			current_tech = player.science_system.current_research

			# iterate techs in order
			for tech_name in player.science_system.techs:
				tech = player.science_system.techs[tech_name]
				if tech_name not in unlocked_techs:
					# Check prerequisites
					if tech.can_research(unlocked_techs):
						# Check if player has progress < 50% (assuming research progress is between 0-100)
						# We need a way to check progress per tech, but assuming here:
						progress = player.science_system.get_progress_for_tech(tech_name)
						if progress < 50:
							player.science_system.complete_tech(tech_name)
							player.science_system.set_current_research(None)
							player.game.show_message(f"Ancient Ruins completed tech: {tech_name}", 90)
							break

		elif self.effect_id == 8:
			player.culture += 20

		tile.ancient_ruin = None

class Pantheon:
	def __init__(self, name, effect_text):
		self.name = name
		self.desc = effect_text		