
#here is city.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

from data import dictionary, constants
from entities import Building
from utils import helper, BoolResult
from systems import ProductionSystem

import math
import heapq
from itertools import combinations
from collections import deque, defaultdict

class City:
	_id_counter = 0  # class-level variable for unique ID assignment
	PURCHASE_COST = 55

	def __init__(self, q, r, player):
		self.id = City._id_counter
		City._id_counter += 1
		
		if City._id_counter < len(constants.CITY_NAMES):
			self.name = constants.CITY_NAMES[City._id_counter]
		else:
			self.name = f"City{City._id_counter}"
			
		self.q = q
		self.r = r
		self.is_capital = False
		self.has_city_connection = False
		self.owner = player
		self.population = 1
		self.food = 0  # accrued food basket
		self.worked_tiles = set()
		self.aqueduct_basket = 0
		
		self.production_system = ProductionSystem(self)
		self.local_happiness = 0
		self.buildings = []
		self.stored_culture = 0
		self.border_expansions = 0		

	@property
	def food_per_turn(self):
		if self.current_project_name == "Settler":
			return 0

		positive = 0
		for tile in self.worked_tiles:
			positive += tile.food

		positive += sum(b.food for b in self.buildings)

		if "Landed Elite" in self.owner.unlocked_policies and self.is_capital:
			positive += 2

		# Temple of Artemis: +10% BASE food empire-wide
		if "Temple of Artemis" in self.owner.wonders:
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

		# --- Tradition finisher---
		required_policies = [
			"Tradition",
			"Aristocracy",
			"Oligarchy",
			"Legalism",
			"Landed Elite",
			"Monarchy"
		]


		if (all(p in self.owner.unlocked_policies for p in required_policies) and self in self.owner.cities[:4]): #this might not work if we can LOSE cities...
			growth_modifier += 0.15

		return growth_modifier * difference if difference >= 0 else difference

	@property
	def food_needed_for_growth(self):
		n = self.population
		return 15 + 8 * (n - 1) + (n - 1) ** 1.5 #floored?

	def process_growth(self, engine):
		if self.current_project_name == "Settler":
			pass

		elif self.food_per_turn >= 0:
			self.food += self.food_per_turn
			if any("Aqueduct" in b.name for b in self.buildings):
				self.aqueduct_basket += self.food_per_turn
				if self.aqueduct_basket > self.food_needed_for_growth * 0.4:
					self.aqueduct_basket = self.food_needed_for_growth * 0.4 #for THIS growth or NEXT growth?

			# Check for population growth, if instead of while?
			while self.food >= self.food_needed_for_growth:
				self.food -= self.food_needed_for_growth
				self.population += 1
				self.update_worked_tiles(engine)

				if any("Aqueduct" in b.name for b in self.buildings):
					self.food += self.aqueduct_basket
					self.aqueduct_basket = 0

		else:
			# Starvation
			if self.food + self.food_per_turn < 0:
				if self.population > 1:
					self.population -= 1
					self.food = 0
					self.aqueduct_basket = 0
				else:
					self.food = 0
					self.aqueduct_basket = 0
			else:
				self.food += self.food_per_turn

	@property
	def production_per_turn(self):
		worked_production = sum(tile.production for tile in self.worked_tiles)
		unassigned_workers = self.population - len(self.worked_tiles)
		bonus_from_unemployed = max(0, unassigned_workers) * 1
		from_buildings = sum(b.production for b in self.buildings if b.completed)

		total = worked_production + bonus_from_unemployed + from_buildings

		if "Republic" in self.owner.unlocked_policies:
			total += 1

		if self.owner.pantheon == "God-King" and self.is_capital == True:
			total += 1

		if self.owner.pantheon == "God of Craftsmen" and self.population >= 3:
			total += 1			

		percent_modifier = 1

		if "Republic" in self.owner.unlocked_policies and isinstance(self.production_system.current_project, Building):
			percent_modifier += 0.05

		if "Aristocracy" in self.owner.unlocked_policies and isinstance(self.production_system.current_project, Building) and self.production_system.current_project.wonder:
			percent_modifier += 0.15 #correct? also not for national wonders right		

		if self.owner.in_golden_age:
			percent_modifier += 0.2

		if self.owner.happiness < 0:
			percent_modifier -= 0.02 * self.owner.happiness	

		return percent_modifier * total

	@property
	def current_project_name(self):
		if self.production_system.current_project:
			return self.production_system.current_project.name
		return None

	@property
	def culture(self):
		culture = sum(b.culture for b in self.buildings)

		if "Liberty" in self.owner.unlocked_policies:
			culture += 1

		if "Tradition" in self.owner.unlocked_policies and self.is_capital:
			culture += 3

		if self.owner.pantheon == "God-King" and self.is_capital:
			culture += 1

		return culture

	@property
	def science(self):
		base_science = self.population
		base_science += sum(b.science for b in self.buildings)
		base_science += self.population // 2 if any(b.name == "Library" for b in self.buildings) else 0

		if self.owner.pantheon == "God-King" and self.is_capital == True:
			base_science += 1

		if self.owner.pantheon == "Messenger of the Gods" and self.has_city_connection:
			base_science += 2

		percent_modifier = 1
		percent_modifier += sum(b.science_percentage for b in self.buildings)

		return math.floor(base_science * percent_modifier ) #ceiling?

	@property
	def faith(self):
		faith = sum(b.faith for b in self.buildings)

		if self.owner.pantheon == "God-King" and self.is_capital:
			faith += 1				

		return faith

	@property
	def gold(self):
		from_tiles = sum(tile.gold for tile in self.worked_tiles)
		from_buildings = sum(b.gold for b in self.buildings)

		total_gold = from_tiles + from_buildings

		if self.owner.pantheon == "God-King" and self.is_capital:
			total_gold += 1

		percent_modifier = 1
		percent_modifier += sum(b.gold_percentage for b in self.buildings)

		if "Commerce" in self.owner.unlocked_policies:
			percent_modifier += 0.25

		#add trade route gold here?

		return percent_modifier * total_gold

	def can_purchase_tile(self, tile, engine):
		if not helper.in_bounds(tile.q, tile.r):
			return BoolResult(False, "Tile out of bounds.")

		if tile.owner is not None:
			return BoolResult(False, "Tile already owned by someone")

		if helper.hex_distance(self.q, self.r, tile.q, tile.r) > 3:
			return BoolResult(False, "Tile is too far from the city (must be within 3 tiles).")

		if not helper.is_adjacent_to_owned_tile(tile, self.owner, engine):
			return BoolResult(False, "Tile must be adjacent to your city's borders.")

		if self.owner.gold < self.PURCHASE_COST:
			return BoolResult(False, f"Not enough gold to purchase tile (cost: {self.PURCHASE_COST}).")

		return BoolResult(True, "Can purchase tile")

	def purchase_tile(self, tile, engine):
		if not (result := self.can_purchase_tile(tile, engine)):
			return result

		self.owner.gold -= self.PURCHASE_COST
		tile.owner = self.owner

		return BoolResult(True, f"Tile purchased for {self.PURCHASE_COST}g!")

	def get_purchasable_tiles(self, engine):
		purchasable_tiles = []
		for dq in range(-3, 4):
			for dr in range(-3, 4):
				q = self.q + dq
				r = self.r + dr

				if 0 <= q < len(engine.tiles) and 0 <= r < len(engine.tiles[0]):
					tile = engine.tiles[q][r]
					if self.can_purchase_tile(tile, engine):
						purchasable_tiles.append(tile)

		return purchasable_tiles

	def update_worked_tiles(self, engine):
		city_tile = engine.tiles[self.q][self.r]

		self.worked_tiles = set()

		workable_tiles = [
			tile for row in engine.tiles for tile in row
			if tile.owner == self.owner and
			(tile.q, tile.r) != (self.q, self.r) and
			helper.hex_distance(self.q, self.r, tile.q, tile.r) <= 3
		]

		#would need to add other players here
		other_worked_tiles = set()
		for city in self.owner.cities:
			if city is not self:
				other_worked_tiles.update(city.worked_tiles) #append?

		available_tiles = [
			tile for tile in workable_tiles if tile not in other_worked_tiles
		]

		available_tiles.sort(key=lambda t: t.food + t.production, reverse=True)

		tiles_to_work = available_tiles[:self.population]

		for tile in tiles_to_work:
			tile.worked_by = self
			self.worked_tiles.add(tile)
			
		#theres the tile flag worked by, AND the city list...
		self.worked_tiles.add(city_tile)
		city_tile.worked_by = self

	def get_workable_tiles(self, engine):
		territory_tiles = [
			tile for row in engine.tiles for tile in row
			if tile.owner == self.owner and
			(tile.q, tile.r) != (self.q, self.r) and
			helper.hex_distance(self.q, self.r, tile.q, tile.r) <= 3
		]

		# Exclude tiles worked by other cities
		other_worked_tiles = set()
		for player in engine.players:
			for city in player.cities:
				if city is not self:
					other_worked_tiles.update(city.worked_tiles)

		workable = {
			tile for tile in territory_tiles if tile not in other_worked_tiles
		}

		return workable

	def can_assign_tile(self, tile, engine):
		if tile.q == self.q and tile.r == self.r:
			return BoolResult(False, "City tile is always worked and cannot be assigned")
		if len(self.worked_tiles) >= (self.population + 1):
			return BoolResult(False, "All citizens are already assigned")
		if tile not in self.get_workable_tiles(engine):
			return BoolResult(False, f"Tile at ({tile.q},{tile.r}) is not valid to assign")
		return BoolResult(True, "Tile can be assigned")

	def assign_tile(self, tile, engine):
		if not (result := self.can_assign_tile(tile, engine)):
			return result

		#theres the tile flag worked by, AND the city list...
		self.worked_tiles.add(tile)
		tile.worked_by = self
		return BoolResult(True, "Tile assigned")

	def can_unassign_tile(self, tile):
		if tile.q == self.q and tile.r == self.r:
			return BoolResult(False, "City tile cannot be unassigned")
		elif tile in self.worked_tiles:
			return BoolResult(True, "Tile can be unassigned")
		return BoolResult(False, f"Tile at ({tile.q},{tile.r}) was not worked")

	def unassign_tile(self, tile):
		if not (result := self.can_unassign_tile(tile)):
			return result
		
		#theres the tile flag worked by, AND the city list...
		self.worked_tiles.remove(tile)
		tile.worked_by = None
		return BoolResult(True, "Tile unassigned")

	def can_purchase_building(self, building_name, player):
		building_data = dictionary.BUILDINGS.get(building_name)
		if not building_data:
			return BoolResult(False, "Building not found.")

		if any(b.name == building_name for b in self.buildings):
			return BoolResult(False, "Building already constructed.")               

		required_techs = building_data.get("techs_required", [])
		player_techs = player.science_system.unlocked_techs

		if any(tech not in player_techs for tech in required_techs):
			return BoolResult(False, f"You don't have the required technology to build {building_name}.")

		gold_cost = building_data.get("gold_cost", 0)
		if gold_cost <= 0:
			return BoolResult(False, "This building cannot be purchased.")

		if player.gold < gold_cost:
			return BoolResult(False, "Not enough gold.")

		return BoolResult(True, "Building can be purchased")

	def purchase_building(self, building_name, player):
		if not (result := self.can_purchase_building(building_name, player)):
			return result

		building_data = dictionary.BUILDINGS.get(building_name) #lookup twice...
		gold_cost = building_data.get("gold_cost", 0)
		player.gold -= gold_cost

		building_obj = helper.build_building_object(building_name, building_data)
		self.buildings.append(building_obj)

		if self.current_project_name == building_name:
			self.production_system.current_project = None

		return BoolResult(True, f"Purchased {building_name}.")

	def can_purchase_unit(self, name, player):
		unit_data = dictionary.UNITS.get(name)
		if not unit_data:
			return BoolResult(False, "Unit not found.")

		gold_cost = unit_data.get("gold_cost", 0)
		if gold_cost <= 0:
			return BoolResult(False, "This unit cannot be purchased.")
		
		if player.gold < gold_cost:
			return BoolResult(False, "Not enough gold.")

		return BoolResult(True, "Can purchase unit")

	def purchase_unit(self, name, player):
		if not (result := self.can_purchase_unit(name, player)):
			return result

		player.gold -= gold_cost
		engine.spawn_unit(player, name, self.q, self.r)

		return BoolResult(True, f"Purchased {name}.")

	def compute_influence_distance(city, engine, max_range=5):
		visited = set()
		distances = {}
		start_coords = (city.q, city.r)
		heap = [(0, start_coords)]

		while heap:
			dist, (q, r) = heapq.heappop(heap)
			if (q, r) in visited:
				continue

			visited.add((q, r))
			if helper.hex_distance(city.q, city.r, q, r) > max_range:
				continue

			tile = engine.tiles[q][r]
			cost = INFLUENCE_COST.get(tile.terrain_type, 1)
			mod_cost = max(1, min(3, cost))  # Clamp between 1 and 3
			total = dist + mod_cost
			distances[(q, r)] = total

			for nq, nr in helper.hex_neighbors(q, r):
				if (nq, nr) not in visited:
					heapq.heappush(heap, (total, (nq, nr)))
		return distances

	def compute_tile_priority(tile, engine):
		dist = helper.hex_distance(tile.q, tile.r, self.q, self.r) * MULTIPLIERS["DISTANCE"]

		influence_base = constants.TERRAIN_INFLUENCE_COST[tile.terrain_type]
		
		#pull values from constants?
		if tile.trees == 1 or tile.trees == 2 or tile.elevation == 1 or tile.resource == "swamp":
			influence_base = 1
		elif tile.elevation == 2 or tile.resource == "ice":
			influence_base = 3
		elif tile.resource == "oasis" or tile.resource == "atoll" or tile.resource == "flood plains": #fp resource or feature?
			influence_base = -1
			
		influence_base *= dist * constants.MULTIPLIERS["RESOURCE"]
		
		if tile.resource: #an ACTUAL resource not swamp or flood plains i think... or nat wonders...
			influence_base *= constants.MULTIPLIERS["RESOURCE"]
		if tile.terrain_type in ("c", "l", "o"):
			influence_base *= constants.MULTIPLIERS["WATER"]
		if tile.elevation == 2:
			influence_base *= constants.MULTIPLIERS["UNWORKABLE"]
		if tile.improvement: #like forts?
			influence_base *= constants.MULTIPLIERS["IMPROVEMENT"]
		#if tile.barbarian_camp:
			#infleunce_base *= constants.MULTIPLIERS["BARB_CAMP"]	
		if tile.road_complete:
			influence_base *= constants.MULTIPLIERS["ROAD"]		
		if tile.resource == "kailash":
			influence_base *= constants.MULTIPLIERS["NATURAL_WONDER"]
		if sum(tile.food, tile.production, tile.science, tile.gold, tile.culture, tile.faith) > 0: #unsure about logic
			influence_base *= sum(tile.food, tile.production, tile.science, tile.gold, tile.culture, tile.faith) * constants.MULTIPLIERS["YEILD POINT"]
		if not helper.is_adjacent_to_owned_tile(tile, self.owner, engine):
			influence_base *= constants.MULTIPLIERS["NO_ADJACENT_OWNED"]

		return influence_base

	def gain_culture(self, amount):
		self.stored_culture += amount
		if self.stored_culture >= self.border_growth_threshold:
			return self.expand_borders()
		return BoolResult(False, "Not enough culture for border expansion yet.")	

	def expand_borders(self, engine):
		#if self.stored_culture < self.border_growth_threshold:
			#return BoolResult(False, "Insufficient culture to expand borders.")

		#tile_priorities = []
		#for tile within 6 distance of city? expensive...:
			#tile_priorities.append(tile, self.compute_tile_priority(tile, engine))
		
		#if tile_priorities.length == 0:
			#return BoolResult(False, "No valid tile to expand into.")

		#best_tile = lowest priority in tile_priorities

		#best_tile.owner = self.owner
		#self.stored_culture -= self.border_growth_threshold
		#self.border_expansions += 1

		return BoolResult(True, "Borders expanded")

	@property
	def border_growth_threshold(self):
		base_threshold = 15 * (self.border_expansions + 1) #probably not accurate

		if "Tradition" in self.owner.social_policies:
			return base_threshold // 2 #probably not accurate

		return base_threshold