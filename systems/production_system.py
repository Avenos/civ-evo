
from utils import helper
from data import dictionary
from entities import Building

class ProductionSystem:
	def __init__(self, city):
		self.city = city

		#is this available or all or what?
		self.building_projects = [helper.build_building_object(name, data) for name, data in dictionary.BUILDINGS.items()]
		self.unit_projects = [helper.build_unit_object(name, data) for name, data in dictionary.UNITS.items()]

		self.projects = self.building_projects + self.unit_projects

		self.current_project = None  # Can be building or unit (store as a dict/object)

	#every state change, we are checking through EVERY building that exists to see if we can build it? really? whenever they become available just append to list? hmmmm, but there are other factors...
	def can_choose_project(self, project):
		from entities import Unit

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
					if c.production_system.current_project and c.production_system.current_project.name == project_name and c is not self.city:
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
					if not any("Colisseum" in b.name for b in city.buildings):
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

		if isinstance(project, Unit) and project_name == "Settler" and self.city.population < 2:
			return False, "Settler cannot be built unless city population is at least 2."

		return True, "Can choose project"

	def get_available_projects(self):
		seen = set()
		available = []

		for proj in self.projects:
			if proj.name in seen:
				continue

			success, message = self.can_choose_project(proj)
			if success:
				available.append(proj)
				seen.add(proj.name)

		return available

	def choose_project(self, project_name):
		from entities import Unit

		player = self.city.owner

		# Always create a fresh instance of the selected project
		if project_name in dictionary.UNITS:
			project_data = dictionary.UNITS[project_name]
			project = helper.build_unit_object(project_name, project_data)
		elif project_name in dictionary.BUILDINGS:
			project_data = dictionary.BUILDINGS[project_name]
			project = helper.build_building_object(project_name, project_data)
		else:
			return False, f"Project data for '{project_name}' not found."

		# Validate that project can be started now
		success, message = self.can_choose_project(project)
		if not success:
			return False, message

		# Assign freshly created project
		self.current_project = project
		return True, f"Started {project_name}."

	def apply_production(self, engine):
		from entities import Unit
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

	def complete_building(self, building_name):
		for b in self.building_projects:
			if b.name == building_name:
				b.completed = True
				b.progress = b.production_cost
				self.city.buildings.append(b)

				if b.wonder:
					self.city.owner.wonders.append(b.name) #append right func?

				if building_name == "Hanging Gardens":
					garden = helper.create_building("Garden")
					garden.completed = True
					garden.progress = garden.production_cost
					self.city.buildings.append(garden)

				return

	def complete_unit(self, unit_name, q, r, engine):
		engine.spawn_unit(self.city.owner, unit_name, q, r)
		#do something to complete PROJECT here?