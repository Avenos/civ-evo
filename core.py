
import dictionary
import helper
import math
from collections import deque
from systems import ProductionSystem
from constants import CITY_NAMES

class Tile:
	def __init__(self, q, r, terrain_type, elevation, trees, resource):
		self.q = q
		self.r = r
		self.terrain_type = terrain_type
		self.elevation = elevation
		self.trees = trees
		self.resource = resource
		self.city = None
		self.owner = None
		self.improvement = None
		self.improvement_progress = 0  # turns worked on improvement
		self.road = 0
		self.road_progress = 0
		self.unit = None  # or maybe a list if you support stacking in the future
		self.rivers = set()  # Set of edge indices (0 through 5) with rivers
		self.ancient_ruin = None

		#base yields
		terrain_data = dictionary.TERRAIN_TYPES[terrain_type]

		#bonus from resources
		#resource_data = dictionary.RESOURCES.get(resource, dictionary.RESOURCES["n"])

		if self.elevation == 2 or self.terrain_type in ("ocean", "coast"):
			self.movement_cost = 0
			self.passable = 0
		elif self.elevation == 1 or self.trees in (1, 2):
			self.movement_cost = 2
			self.passable = 1
		else:
			self.movement_cost = 1
			self.passable = 1

		self.food = terrain_data.get("food", 0)
		self.production = terrain_data.get("production", 0)

		self.gold = 0
		self.science = 0
		self.culture = 0
		self.faith = 0


class City:
	name_index = 0  # shared across all City instances

	def __init__(self, q, r, player):
		if City.name_index < len(CITY_NAMES):
			self.name = CITY_NAMES[City.name_index]
			City.name_index += 1
		else:
			self.name = f"City{City.name_index}"
			City.name_index += 1
		self.q = q
		self.r = r
		self.is_capital = 0
		self.owner = player
		self.population = 1
		self.food = 0 # accrued food basket
		self.production_system = ProductionSystem(self)
		self.local_happiness = 0
		self.buildings = []
		self.worked_tiles = set()  # tiles worked (Tile objects)

	@property
	def has_city_connection(self):
		if self.is_capital:
			return False

		# Find the capital city for this player
		capital = None
		for city in self.owner.cities:
			if city.is_capital:
				capital = city
				break

		if not capital:
			# No capital found, so no connection
			return False

		from your_helper_module import has_city_connection_to_capital, get_neighboring_tiles  # import appropriately

		# Assuming you have a global or accessible list of all tiles in game
		all_tiles = ... # define or access your all tiles list here

		return has_city_connection_to_capital(self, capital, all_tiles)

	@property
	def food_per_turn(self):
		granary_bonus_resources = {"wheat", "deer", "bananas"}
		sun_god_bonus_resources = {"wheat", "citrus", "bananas"}
	
		# Compute base food from worked tiles, with Granary bonuses
		positive = 0
		for tile in self.worked_tiles:
			tile_food = tile.food
			if any("Granary" in b.name for b in self.buildings) and getattr(tile, "resource", None) in granary_bonus_resources:
				tile_food += 1
			if self.owner.pantheon == "Sun God" and getattr(tile, "resource", None) in sun_god_bonus_resources:
				tile_food += 1
			
			positive += tile_food
	
		# Add food from buildings
		positive += sum(b.food for b in self.buildings)
		
		if "Landed Elite" in self.owner.unlocked_policies and self.is_capital:
			positive += 2
	
		# Temple of Artemis: +10% total food empire-wide
		if any("Temple of Artemis" in b.name for city in self.owner.cities for b in city.buildings):
			positive *= 1.10
	
		# Subtract population consumption
		negative = 2 * self.population
		difference = positive - negative
	
		# Growth modifiers (apply only to surplus food)
		growth_modifier = 1.0
		if self.owner.happiness < 0:
			growth_modifier -= 0.75
			
		if "Landed Elite" in self.owner.unlocked_policies and self.is_capital:
			growth_modifier += 0.1
			
		if self.owner.pantheon == "Fertility Rites":
			growth_modifier += 0.1			
	
		for building in self.buildings:
			growth_modifier += building.growth_percentage
	
		return growth_modifier * difference if difference >= 0 else difference


	@property
	def food_needed_for_growth(self):
		n = self.population
		return 15 + 8 * (n - 1) + (n - 1) ** 1.5

	@property
	def culture(self):
		culture = sum(b.culture for b in self.buildings)

		if "Liberty" in self.owner.unlocked_policies:
			culture += 1

		# Check if the city has a building named "Palace"
		if "Tradition" in self.owner.unlocked_policies and any(b.name == "Palace" for b in self.buildings):
			culture += 3

		if self.owner.pantheon == "God-King" and self.is_capital == True:
			culture += 1

		return culture


	@property
	def science(self):
		base_science = self.population

		flat_building_science = sum(b.science for b in self.buildings)

		has_library = any(b.name == "Library" for b in self.buildings)
		library_bonus = self.population // 2 if has_library else 0

		raw_science = base_science + flat_building_science + library_bonus

		if self.owner.pantheon == "God-King" and self.is_capital == True:
			raw_science += 1		

		total_percentage = sum(b.science_percentage for b in self.buildings)
		bonus_from_percentage = raw_science * total_percentage

		return math.floor(raw_science + bonus_from_percentage) #ceiling?

	@property
	def faith(self):
		faith = sum(b.faith for b in self.buildings)

		if self.owner.pantheon == "God-King" and self.is_capital == True:
			faith += 1				

		return faith

	@property
	def gold(self):
		from_tiles = sum(tile.gold for tile in self.worked_tiles)
		from_buildings = sum(b.gold for b in self.buildings)
	
		golden_age_bonus = 0
		if self.owner.in_golden_age:
			golden_age_bonus = sum(1 for tile in self.worked_tiles if tile.gold >= 1)
	
		total_gold = from_tiles + from_buildings + golden_age_bonus
		if self.owner.pantheon == "God-King" and self.is_capital:
			total_gold += 1
	
		percentage_modifier = 1.0
		if "Commerce" in self.owner.unlocked_policies:
			percentage_modifier += 0.25
	
		return percentage_modifier * total_gold


	@property
	def production_per_turn(self):
		worked_production = sum(tile.production for tile in self.worked_tiles)
		unassigned_workers = self.population - len(self.worked_tiles)
		bonus_from_unemployed = max(0, unassigned_workers) * 1  # +1 per idle pop
		from_buildings = sum(b.production for b in self.buildings if b.completed)

		total = worked_production + bonus_from_unemployed + from_buildings

		if "Republic" in self.owner.unlocked_policies:
			total += 1

		if self.owner.pantheon == "God-King" and self.is_capital == True:
			total += 1

		percentage_modifier = 1

		if "Republic" in self.owner.unlocked_policies and isinstance(self.production_system.current_production, Building):
			percentage_modifier += 0.05

		if self.owner.in_golden_age:
			percentage_modifier += 0.2

		if self.owner.happiness < 0:
			percentage_modifier += 0.02 * self.owner.happiness		

		return percentage_modifier * total

	@property
	def current_production_name(self):
		if self.production_system.current_project:
			return self.production_system.current_project.name
		return None

	def complete_building(self, building_name):
		for b in self.production_system.building_projects:  # ONLY buildings here
			if b.name == building_name:
				b.completed = True
				b.progress = b.production_cost
				self.buildings.append(b)
				return

	def complete_unit(self, unit_name, q, r, engine):
		engine.spawn_unit(player=self.owner, q=q, r=r, name=unit_name)
		print(f"[DEBUG] Spawned unit '{unit_name}' at city ({self.q},{self.r}) for player '{self.owner.name}'.")


	def update_worked_tiles(self, game):
		city_tile_coords = (self.q, self.r)

		# All tiles within 3 hexes (including city tile)
		territory_tiles = [
			t for t in game.territory
			if helper.hex_distance(self.q, self.r, *t) <= 3
		]

		# Gather tiles worked by other cities (all players)
		other_worked_tiles = set()
		for player in game.players:
			for city in player.cities:
				if city is not self:
					other_worked_tiles.update(city.worked_tiles)

		# Exclude tiles worked by others, except city tile which is always yours
		available_tiles = [t for t in territory_tiles if t not in other_worked_tiles and t != city_tile_coords]

		# Sort available tiles by combined food + production descending
		available_tiles.sort(
			key=lambda coords: game.tiles[coords[0]][coords[1]].food + game.tiles[coords[0]][coords[1]].production,
			reverse=True
		)

		# Start with city tile (always worked)
		chosen_coords = [city_tile_coords]

		# Add tiles up to population count (not including city tile)
		chosen_coords.extend(available_tiles[:self.population])

		# Convert coords to tile objects
		self.worked_tiles = set(game.tiles[q][r] for q, r in chosen_coords)

	def process_growth(self):
		if self.current_production_name == "Settler":
			pass
		elif self.food_per_turn >= 0:
			self.food += self.food_per_turn
			# Check for population growth
			while self.food >= self.food_needed_for_growth:
				self.food -= self.food_needed_for_growth
				self.population += 1
		else:
			# Starvation check: if basket can't cover deficit, lose pop
			if self.food + self.food_per_turn < 0:
				if self.population > 1:
					self.population -= 1
					self.food = 0
				else:
					self.food = 0  # Cannot go below 1 pop
			else:
				self.food += self.food_per_turn  # Lose food, but not enough to starve

	def purchase_building(self, building_name, player):
		building_data = dictionary.BUILDINGS.get(building_name)
		if not building_data:
			return False, "Building not found."

		if any(b.name == building_name for b in self.buildings):
			return False, "Building already constructed."                

		required_techs = building_data.get("techs_required", [])
		player_techs = player.science_system.unlocked_techs

		if any(tech not in player_techs for tech in required_techs):
			return False, f"You don't have the required technology to build {building_name}."

		gold_cost = building_data.get("gold_cost", 0)
		if gold_cost <= 0:
			return False, "This building cannot be purchased."

		if player.gold < gold_cost:
			return False, "Not enough gold."

		# Deduct gold
		player.gold -= gold_cost

		# Use helper
		building_obj = helper.create_building(building_name, building_data)
		self.buildings.append(building_obj)

		print(f"Buildings in {self.name}: {[b.name for b in self.buildings]}")

		return True, f"Purchased {building_name}."


	def purchase_unit(self, name, player):
		# Check if unit exists in your dictionary
		unit_data = dictionary.UNITS.get(name)
		if not unit_data:
			return False, "Unit not found."

		gold_cost = unit_data.get("gold_cost", 0)
		if player.gold < gold_cost:
			return False, "Not enough gold."

		# Deduct gold from player
		player.gold -= gold_cost

		# Create and add the new unit at the city location
		new_unit = Unit(name, player, self.q + 1, self.r + 1)


		game.tiles[q][r].unit = new_unit
		player.units.append(new_unit)  # or engine.units.append(new_unit)

		return True, f"Purchased {name}."

	def has_building(self, name):
		return any(b.name == name for b in self.buildings)        


class Building:
	def __init__(self, name, food=0, production=0, gold=0, maintenance=0, science=0, culture=0, faith =0, happiness=0, growth_percentage=0, science_percentage=0, production_cost=0, gold_cost=0, techs_required=None, policies_required=None):
		self.name = name
		self.type = "building"
		self.food = food
		self.production = production
		self.gold = gold
		self.maintenance = maintenance
		self.science = science
		self.culture = culture
		self.faith = faith
		self.happiness = happiness
		self.growth_percentage = growth_percentage
		self.science_percentage = science_percentage  # capital bonus?
		self.production_cost = production_cost
		self.producable = gold_cost > 0
		self.gold_cost = gold_cost
		self.purchasable = gold_cost > 0

		self.techs_required = techs_required or []
		self.policies_required = policies_required or []

		self.progress = 0
		self.completed = False

	def reset_progress(self):
		self.progress = 0
		self.completed = False                

class Unit:
	def __init__(self, name, player=None, q=None, r=None, hp=100, moves=2, gold_cost=0, production_cost=0, techs_required=None, policies_required=None):
		self.name = name
		self.player = player
		self.type = "unit"
		self.q = int(q) if q is not None else None
		self.r = int(r) if r is not None else None

		self.hp = hp
		self.moves = moves
		self.moves_left = moves
		self.gold_cost = gold_cost
		self.production_cost = production_cost
		self.techs_required = techs_required or []
		self.policies_required = policies_required or []

		self.progress = 0
		self.completed = False

		if player and q is not None and r is not None:
			player.units.append(self)

	def move_to(self, from_tile, to_tile):
		if self.moves_left == 0:
			return "No moves left!"
	
		if helper.hex_distance(from_tile.q, from_tile.r, to_tile.q, to_tile.r) > 1:
			return "Can only move to adjacent tiles."
	
		if to_tile.passable == 0:
			return "Impassable tile."
	
		# water tile check here (if needed)
	
		if to_tile.unit is not None:
			return "Tile already occupied."
	
		if self.name == "Scout":
			# Scouts ignore all movement penalties
			print("Scout ignores terrain and river movement costs.")
			self.moves_left -= 1
		else:
			# Non-Scout movement logic
			if helper.has_river_between(from_tile, to_tile):
				print(f"River detected between ({from_tile.q},{from_tile.r}) and ({to_tile.q},{to_tile.r})")
				self.moves_left = 0
			else:
				self.moves_left -= 1
	
			if to_tile.elevation == 1 or to_tile.trees != 0:
				self.moves_left = 0
	
		# Move the unit
		from_tile.unit = None
		to_tile.unit = self
	
		self.q = to_tile.q
		self.r = to_tile.r
	
		if to_tile.ancient_ruin is not None:
			ruin = to_tile.ancient_ruin
			ruin.trigger(self.player, to_tile)
			print(f"Ancient Ruins triggered: {ruin.description}")
	
		return True


	def improve_tile(self, tile, new_improvement=None, game=None):
		if self.name != "Worker":
			return "Only Workers can improve tiles."

		if self.moves_left < 1:
			return "Not enough movement points to improve."

		# If a new improvement is requested (overwrite existing one)
		if new_improvement:
			imp_data = dictionary.IMPROVEMENTS.get(new_improvement)
			if not imp_data:
				return f"Unknown improvement '{new_improvement}'."

			if tile.terrain not in imp_data["allowed_terrains"]:
				return f"Cannot build {new_improvement} on {tile.terrain}."

			# Overwrite the existing improvement and reset progress
			tile.improvement = new_improvement
			tile.improvement_progress = 0
			# Use 1 move to start working on the new improvement immediately
			tile.improvement_progress += 1
			self.moves_left -= 1

			if tile.improvement_progress >= imp_data["turns_required"]:
				if game:
					game.show_message(f"{new_improvement.capitalize()} completed on tile ({tile.q}, {tile.r})!", 90)
				tile.improvement_progress = imp_data["turns_required"]
				return True  # finished immediately if 1 turn only

			return False  # started improvement, still working

		# No new improvement requested, continue working on current improvement
		if not tile.improvement:
			return "No improvement assigned to this tile."

		imp_data = dictionary.IMPROVEMENTS.get(tile.improvement)
		if not imp_data:
			return "Invalid improvement on tile."

		tile.improvement_progress += 1
		self.moves_left -= 1

		if tile.improvement_progress >= imp_data["turns_required"]:
			if game:
				game.show_message(f"{tile.improvement.capitalize()} completed on tile ({tile.q}, {tile.r})!", 90)
			tile.improvement_progress = imp_data["turns_required"]
			return True  # finished

		return False  # still working


	def reset_turn(self):
		self.moves_left = 2