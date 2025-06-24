
import helper
import dictionary
from core import Building

class ProductionSystem:
	def __init__(self, city):
		self.city = city

		#is this available or all or what?
		self.building_projects = [helper.build_building_object(name, data) for name, data in dictionary.BUILDINGS.items()]
		self.unit_projects = [helper.build_unit_object(name, data) for name, data in dictionary.UNITS.items()]

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

		if isinstance(project, Building):
			missing_building = next((req for req in project.buildings_required if req not in [b.name for b in self.city.buildings]), None)
			if missing_building:
				return False, f"Building requirement '{missing_building}' not met for '{project_name}'."

			if project.wonder or project.national_wonder:
				for c in self.city.owner.cities: #needs adapted for multiple players
					if any(b.name == project_name for b in c.buildings):
						return False, f"{project_name} already exists somewhere in the world."
					if c.current_project and c.current_project.name == project_name and c is not self.city:
						return False, f"{project_name} is already being constructed in another city."

			if project_name == "Monument":
				if any("Monument (FREE)" in b.name for b in self.city.buildings):
					return False, "A Monument is already present in the city."

			if project_name == "National College":
				for city in player.cities:
					has_library = any("Library" in b.name for b in city.buildings)
					if not has_library:
						return False, "National College requires a completed Library in all cities."
	
			if project_name == "Circus Maximus":
				for city in player.cities:
					has_colisseum = any("Colisseum" in b.name for b in city.buildings)
					if not has_coliseum:
						return False, "Circus Maximus requires a completed Colisseum in all cities."
	
			if project_name == "Ironworks":
				for city in player.cities:
					has_workshop = any("Workshop" in b.name for b in city.buildings)
					if not has_workshop:
						return False, "Ironworks requires a completed Workshop in all cities."
	
			if project_name == "Observatory":
				city_q, city_r = self.city.q, self.city.r
				tiles = self.city.owner.game.tiles
			
				adjacent_coords = helper.hex_neighbors(city_q, city_r)
			
				has_adjacent_hill = any(tiles[q][r].elevation == 2 for q, r in adjacent_coords)
			
				if not has_adjacent_hill:
					return False, "Observatory can only be built if the city is adjacent to a hill (elevation 2) tile."

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
		from helper import build_unit_object, build_building_object
		import dictionary

		player = self.city.owner

		# Always create a fresh instance of the selected project
		if project_name in dictionary.UNITS:
			project_data = dictionary.UNITS[project_name]
			project = build_unit_object(project_name, project_data)
		elif project_name in dictionary.BUILDINGS:
			project_data = dictionary.BUILDINGS[project_name]
			project = build_building_object(project_name, project_data)
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
		for b in self.building_projects:
			if b.name == building_name:
				b.completed = True
				b.progress = b.production_cost
				self.city.buildings.append(b)

				if building_name == "Hanging Gardens":
					garden_building = helper.create_building("Garden")
					garden_building.completed = True
					garden_building.progress = garden_building.production_cost
					self.city.buildings.append(garden_building)

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
	
	def get_unlocked_names(self): #objects or names?
		return [name for name, tech in self.techs.items() if tech.unlocked]	

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

	def get_available_techs(self):
		available = []
		for name, tech in self.techs.items():
			if tech.unlocked:
				continue
			if all(self.techs[req].unlocked for req in tech.prerequisites):
				available.append(name)
		return available

class AncientRuins:
	RINDS_EFFECTS = {
		1: "Gain 75 gold",
		2: "Gain 20 culture", #only possibly triggers AFTER turn 20
		3: "Gain 1 pop in nearest city",
		4: "Free tech",
		#5: "Gain 20 or 60?? faith ONLY after turn 20",
	}

	def __init__(self, effect_id):
		self.effect_id = effect_id
		self.description = self.RINDS_EFFECTS.get(effect_id, "Unknown effect")

	def trigger(self, player, tile, chosen_effect_id=None, chosen_tech=None):
		effect_id = chosen_effect_id if chosen_effect_id is not None else self.effect_id
	
		valid_effects = {1,2,3,4,5}
		
		if effect_id not in valid_effects:
			raise ValueError(f"Invalid chosen effect ID: {effect_id}")
	
		if effect_id == 1:
			player.gold += 75
	
		elif effect_id == 2:
			player.culture += 20
	
		elif effect_id == 3:
			if not player.cities:
				return
			cities_with_dist = [(hex_distance(tile.q, tile.r, city.q, city.r), city) for city in player.cities]
			cities_with_dist.sort(key=lambda x: x[0])
			min_dist = cities_with_dist[0][0]
			closest_cities = [c for d, c in cities_with_dist if d == min_dist]
	
			city_to_grow = None
			for city in player.cities:
				if city in closest_cities:
					city_to_grow = city
					break
	
			if city_to_grow:
				city_to_grow.population += 1
				city_to_grow.update_worked_tiles(player.game)
	
		elif effect_id == 4:
			unlocked_techs = player.science_system.get_unlocked_names()
			eligible_techs = []
			for tech_name in player.science_system.techs:
				tech = player.science_system.techs[tech_name]
				if tech_name not in unlocked_techs and tech.can_research(unlocked_techs):
					eligible_techs.append(tech_name)
	
			if not eligible_techs:
				# No techs available to complete
				return
	
			# If player didn't specify a tech, pick first eligible by default
			tech_to_complete = chosen_tech if chosen_tech in eligible_techs else eligible_techs[0]
	
			player.science_system.complete_tech(tech_to_complete)
			player.science_system.set_current_research(None)
			player.game.show_message(f"Ancient Ruins completed tech: {tech_to_complete}", 90)
			
		#pantheon after t20?
		
		tile.ancient_ruin = None


class Pantheon:
	def __init__(self, name, effect_text):
		self.name = name
		self.desc = effect_text