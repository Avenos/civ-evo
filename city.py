
import dictionary
import helper
import math
import heapq
from collections import deque, defaultdict
from systems import ProductionSystem
from constants import CITY_NAMES

class City:
	_id_counter = 0  # class-level variable for unique ID assignment

	def __init__(self, q, r, player):
		self.id = City._id_counter
		City._id_counter += 1 #need to set back to 0 on game start?		

		if City._id_counter < len(CITY_NAMES):
			self.name = CITY_NAMES[City._id_counter]
			City._id_counter += 1
		else:
			self.name = f"City{City._id_counter}"
			City._id_counter += 1
		self.q = q
		self.r = r
		self.is_capital = 0
		self.owner = player
		self.population = 1
		self.food = 0 # accrued food basket
		self.production_system = ProductionSystem(self)
		self.local_happiness = 0
		self.buildings = []
		self.stored_culture = 0
		self.border_expansions = 0
		self.worked_tiles = set()  # tiles worked (Tile objects)
		self.aqueduct_basket = 0

	# Influence distance calculator
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

	# Influence priority calculator
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
		# Base cost increments by +15 each time
		base_threshold = 15 * (self.border_expansions + 1)

		# Apply modifiers (e.g., Tradition policy halves cost)
		if "Tradition" in self.owner.social_policies:
			return base_threshold // 2

		return base_threshold


	#do we really need to call this constantly... is that what properties do?
	@property
	def has_city_connection(city, capital, all_tiles):
		if city == capital:
			return True

		visited = set()
		queue = deque()
		queue.append(city.tile)
		visited.add(city.tile)

		while queue:
			current_tile = queue.popleft()
			neighbors = get_neighboring_tiles(current_tile)

			for neighbor in neighbors:
				if neighbor in visited:
					continue

				if neighbor.owner != city.owner:
					continue

				if not neighbor.improvement == "Road":
					continue

				visited.add(neighbor)
				queue.append(neighbor)

				# Check if this neighbor has the capital city
				if neighbor.city == capital:
					return True

		return False

	@property
	def food_per_turn(self):
		if self.current_project_name == "Settler":
			return 0

		positive = 0
		for tile in self.worked_tiles:
			positive += tile.food

		# Add food from buildings
		positive += sum(b.food for b in self.buildings)

		if "Landed Elite" in self.owner.unlocked_policies and self.is_capital:
			positive += 2

		# Temple of Artemis: +10% BASE food empire-wide
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

		if self.owner.pantheon == "God of Craftsmen" and self.population >= 3:
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
	def current_project_name(self):
		if self.production_system.current_project:
			return self.production_system.current_project.name
		return None

	def purchase_tile(self, tile, engine):
		player = self.owner
		q, r = tile.q, tile.r

		# Check if already owned
		if tile.owner is not None:
			return False, "Tile already owned by another player."

		# Check if tile is within 3 tiles of the city
		from helper import hex_distance
		if hex_distance(self.q, self.r, q, r) > 3:
			return False, "Tile is too far from the city (must be within 3 tiles)."

		# Check adjacency to any tile owned by player
		if not helper.is_adjacent_to_owned_tile(tile, player, engine):
			return False, "Tile must be adjacent to your city's borders."

		cost = 55

		if player.gold < cost:
			return False, f"Not enough gold to purchase tile (cost: {cost})."

		# Success — buy tile
		player.gold -= cost
		tile.owner = player

		return True, f"Tile purchased for {cost}g!"


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

		# Mark tiles as being worked by this city
		for tile in self.worked_tiles:
			tile.worked_by = self

	def get_workable_tiles(self, game):
		"""Tiles within 3 hexes, not worked by others, or the city tile itself."""
		city_coords = (self.q, self.r)

		territory_tiles = [
			game.tiles[q][r]
			for q, r in game.territory
			if helper.hex_distance(self.q, self.r, q, r) <= 3
		]

		# Tiles worked by other cities
		other_worked_tiles = set()
		for player in game.players:
			for city in player.cities:
				if city is not self:
					other_worked_tiles.update(city.worked_tiles)

		workable = {
			tile for tile in territory_tiles
			if tile not in other_worked_tiles or (tile.q, tile.r) == city_coords
		}

		return workable


	def set_worked_tiles(self, tiles, game):
		"""EA/manual tile override. Returns (success: bool, message: str)"""
		if len(tiles) > self.population:
			return False, f"Too many tiles assigned: max is {self.population}"

		workable = self.get_workable_tiles(game)
		for tile in tiles:
			if tile not in workable:
				return False, f"Tile at ({tile.q},{tile.r}) is not valid to work"

		self.worked_tiles = set(tiles)
		return True, "Worked tiles updated successfully"


	def unassign_tile(self, tile):
		"""Drop a tile from being worked (manual or as reaction to another city's takeover)."""
		if tile in self.worked_tiles:
			self.worked_tiles.remove(tile)
			return True, f"Tile at ({tile.q},{tile.r}) unassigned"
		return False, f"Tile at ({tile.q},{tile.r}) was not worked"


	def assign_tile(self, tile, game):
		"""Try to add a tile to this city's worked tiles."""
		if len(self.worked_tiles) >= self.population:
			return False, "All citizens are already assigned"

		if tile not in self.get_workable_tiles(game):
			return False, f"Tile at ({tile.q},{tile.r}) is not valid to assign"

		self.worked_tiles.add(tile)
		return True, f"Tile at ({tile.q},{tile.r}) assigned"


	def process_growth(self):
		if self.current_project_name == "Settler":
			pass  # No growth while building settler

		elif self.food_per_turn >= 0:
			self.food += self.food_per_turn

			# Apply stored aqueduct basket food
			if self.aqueduct_basket > 0:
				self.food += self.aqueduct_basket
				self.aqueduct_basket = 0  # Consumed

			# Check for population growth
			while self.food >= self.food_needed_for_growth:
				self.food -= self.food_needed_for_growth
				self.population += 1

				# Handle aqueduct overflow capture if city has one
				if any("Aqueduct" in b.name for b in self.buildings):
					# Save up to 40% of food needed for next pop
					next_food_needed = self.food_needed_for_growth
					self.aqueduct_basket = min(int(next_food_needed * 0.4), self.food)
					self.food -= self.aqueduct_basket

		else:
			# Starvation check: if basket can't cover deficit, lose pop
			if self.food + self.food_per_turn < 0:
				if self.population > 1:
					self.population -= 1
					self.food = 0
					self.aqueduct_basket = 0  # Reset on starvation
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
		building_obj = helper.build_building_object(building_name, building_data)
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
		player.units.append(new_unit)  # is this done already in the unit constructor?

		return True, f"Purchased {name}."

	def has_building(self, name):
		return any(b.name == name for b in self.buildings)        