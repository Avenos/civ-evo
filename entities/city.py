
#here is city.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

from data import dictionary, constants
from entities import Building
from utils import helper
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
		City._id_counter += 1 #need to set back to 0 on game start?		

		if City._id_counter < len(constants.CITY_NAMES):
			self.name = constants.CITY_NAMES[City._id_counter]
			City._id_counter += 1
		else:
			self.name = f"City{City._id_counter}"
			City._id_counter += 1
		self.q = q
		self.r = r
		self.is_capital = False
		self.has_city_connection = False
		self.owner = player
		self.population = 1
		self.food = 0  # accrued food basket
		self.production_system = ProductionSystem(self)
		self.local_happiness = 0
		self.buildings = []
		self.stored_culture = 0
		self.border_expansions = 0
		self.worked_tiles = set()
		self.aqueduct_basket = 0

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

	def process_growth(self):
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
		#city itself?
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
		player = self.owner
		q, r = tile.q, tile.r

		if not helper.in_bounds(q, r):
			return False, "Tile out of bounds."

		if tile.owner is not None:
			return False, "Tile already owned by someone"

		if helper.hex_distance(self.q, self.r, q, r) > 3:
			return False, "Tile is too far from the city (must be within 3 tiles)."

		if not helper.is_adjacent_to_owned_tile(tile, player, engine):
			return False, "Tile must be adjacent to your city's borders."

		if player.gold < self.PURCHASE_COST:
			return False, f"Not enough gold to purchase tile (cost: {self.PURCHASE_COST})."

		return True, None

	def purchase_tile(self, tile, engine):
		success, msg = self.can_purchase_tile(tile, engine)
		if not success:
			return False, msg

		self.owner.gold -= self.PURCHASE_COST
		tile.owner = self.owner

		return True, f"Tile purchased for {self.PURCHASE_COST}g!"

	def get_purchasable_tiles(self, engine):
		purchasable_tiles = []
		for dq in range(-3, 4):
			for dr in range(-3, 4):
				q = self.q + dq
				r = self.r + dr
				
				if 0 <= q < len(engine.tiles) and 0 <= r < len(engine.tiles[0]):
					tile = engine.tiles[q][r]
					can_buy, _ = self.can_purchase_tile(tile, engine)
					if can_buy:
						purchasable_tiles.append(tile)

		return purchasable_tiles

	def update_worked_tiles(self, game):
		city_tile = game.tiles[self.q][self.r]
		city_coords = (self.q, self.r)

		# Collect all tiles within 3 hexes whose owner is the same as the city owner (player)
		owned_tiles = []
		for row in game.tiles:
			for tile in row:
				if tile.owner == self.owner:
					if helper.hex_distance(self.q, self.r, tile.q, tile.r) <= 3:
						owned_tiles.append(tile)

		# Gather tiles worked by other cities (all players)
		other_worked_tiles = set()
		for player in game.players:
			for city in player.cities:
				if city is not self:
					other_worked_tiles.update(city.worked_tiles)

		# Exclude tiles worked by others, except city tile which is always yours
		available_tiles = [t for t in owned_tiles if t not in other_worked_tiles and (t.q, t.r) != city_coords]

		# Sort by food + production
		if self.current_project_name == "Settler": #also make swapping unavailable?
			available_tiles.sort(key=lambda t: t.production + t.science, reverse=True)
		else:
			available_tiles.sort(key=lambda t: t.food + t.production, reverse=True)

		# Start with city tile (always worked)
		chosen_tiles = [city_tile]

		# Add up to pop more tiles
		chosen_tiles.extend(available_tiles[:self.population])

		# Update city worked tiles
		self.worked_tiles = set(chosen_tiles)

		# Mark tiles as worked by this city
		for tile in self.worked_tiles:
			tile.worked_by = self

	def get_workable_tiles(self, game):
		"""Tiles within 3 hexes, owned by this player, and not worked by others (excluding city tile)."""
		city_coords = (self.q, self.r)

		territory_tiles = [
			tile for row in game.tiles for tile in row
			if tile.owner == self.owner and
			(tile.q, tile.r) != city_coords and
			helper.hex_distance(self.q, self.r, tile.q, tile.r) <= 3
		]

		other_worked_tiles = set()
		for player in game.players:
			for city in player.cities:
				if city is not self:
					other_worked_tiles.update(city.worked_tiles)

		workable = {
			tile for tile in territory_tiles if tile not in other_worked_tiles
		}

		return workable

	def can_unassign_tile(self, tile):
		if tile in self.worked_tiles:
			return True, f"Tile can be unassigned"
		return False, f"Tile at ({tile.q},{tile.r}) was not worked"		

	def unassign_tile(self, tile):
		success, message = can_unassign_tile()

		if success:
			self.worked_tiles.remove(tile)
		else:
			return success, message

	def can_assign_tile(self, tile):
		if len(self.worked_tiles) >= self.population:
			return False, "All citizens are already assigned"

		if tile not in self.get_workable_tiles(game):
			return False, f"Tile at ({tile.q},{tile.r}) is not valid to assign"
		
		return True, "Tile can be assigned"

	def assign_tile(self, tile, game):
		self.worked_tiles.add(tile)
		return True, f"Tile assigned"

	def can_purchase_building(self, building_name, player):
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
		
		return True, "Building can be purchased"
	
	def purchase_building(self, building_name, player):
		success, message = self.can_purchase_building(building_name, player)
		
		if not success:
			return success, message

		building_data = dictionary.BUILDINGS.get(building_name) #lookup twice...
		gold_cost = building_data.get("gold_cost", 0)
		player.gold -= gold_cost

		building_obj = helper.build_building_object(building_name, building_data)
		self.buildings.append(building_obj)
		
		if self.current_project_name == building_name:
			self.production_system.current_project = None
		
		return True, f"Purchased {building_name}."

	def can_purchase_unit(self, name, player):
		unit_data = dictionary.UNITS.get(name)
		if not unit_data:
			return False, "Unit not found."

		gold_cost = unit_data.get("gold_cost", 0)
		if player.gold < gold_cost:
			return False, "Not enough gold."
		
		return True, "Can purchase unit"

	def purchase_unit(self, name, player):
		success, message = self.can_purchase_unit(name, player)
		
		if not success:
			return success, message

		player.gold -= gold_cost
		
		engine.spawn_unit(player, name, self.q, self.r)

		return True, f"Purchased {name}."

	def compute_influence_distance(city, game, max_range=5):
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

			tile = game.tiles[q][r]
			cost = INFLUENCE_COST.get(tile.terrain_type, 1)
			mod_cost = max(1, min(3, cost))  # Clamp between 1 and 3
			total = dist + mod_cost
			distances[(q, r)] = total

			for nq, nr in helper.hex_neighbors(q, r):
				if (nq, nr) not in visited:
					heapq.heappush(heap, (total, (nq, nr)))
		return distances

	def compute_tile_priority(tile, dist, game, city):
		priority = dist * MULTIPLIERS["DISTANCE"]

		if tile.resource and tile.resource not in tile.unworkable_resources:
			priority += MULTIPLIERS["RESOURCE"]
		if tile.is_water and not tile.resource:
			priority += MULTIPLIERS["WATER"]
		if tile.unworkable and not tile.resource:
			priority += MULTIPLIERS["UNWORKABLE"]
		if tile.improvement and tile.improvement != "Barbarian Camp":
			priority += MULTIPLIERS["IMPROVEMENT"]
		if tile.improvement == "Barbarian Camp":
			priority += MULTIPLIERS["BARB_CAMP"]
		if tile.has_road:
			priority += MULTIPLIERS["ROAD"]
		if tile.natural_wonder:
			priority += MULTIPLIERS["NATURAL_WONDER"]
		priority += (tile.food + tile.production + tile.gold) * MULTIPLIERS["YIELD_POINT"]

		# Check adjacency
		if not any((nq, nr) in city.territory for nq, nr in helper.hex_neighbors(tile.q, tile.r)):
			priority += MULTIPLIERS["NO_ADJACENT_OWNED"]

		return priority

	def gain_culture(self, amount):
		self.stored_culture += amount
		if self.stored_culture >= self.border_growth_threshold:
			return self.expand_borders()
		return (False, "Not enough culture for border expansion yet.")	

	def expand_borders(self, game):
		if self.stored_culture < self.border_growth_threshold:
			return (False, "Insufficient culture to expand borders.")

		tile = self._select_best_border_tile(game)
		if not tile:
			return (False, "No valid tile to expand into.")

		self.territory.add((tile.q, tile.r))
		self.stored_culture -= self.border_growth_threshold
		self.border_expansions += 1

		return (True, None)

	@property
	def border_growth_threshold(self):
		base_threshold = 15 * (self.border_expansions + 1)

		if "Tradition" in self.owner.social_policies:
			return base_threshold // 2 #probably not accurate

		return base_threshold