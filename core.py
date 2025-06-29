
import dictionary
import helper
import math
import heapq
from collections import deque, defaultdict
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
		self.improvement_progress = 0  # turns worked on improvement...
		self.road = 0
		self.road_progress = 0
		self.unit = None  # or maybe a list if you support stacking in the future
		self.rivers = set()  # Set of edge indices (0 through 5) with rivers
		self.fresh_water = False
		self.ancient_ruin = None
		self.worked_by = None # needs to be set in update tiles?

		#why is this here?
		self.terrain_data = dictionary.TERRAIN_TYPES[terrain_type]
		
		if self.elevation == 2 or self.terrain_type in ("ocean", "coast", "lake"):
			self.movement_cost = 2
			self.passable = 0
		elif self.elevation == 1 or self.trees in (1, 2):
			self.movement_cost = 2
			self.passable = 1
		else:
			self.movement_cost = 1
			self.passable = 1
			
	@property
	def food(self):
		if self.terrain_type == "snow":
			base_food = 0
		elif self.trees == 2: # Jungle
			base_food = 2
		elif self.trees == 1: # Forest
			base_food = 1
		elif self.elevation == 1: # Hill with no trees
			base_food = 0
		else:
			base_food = self.terrain_data.get("food", 0)

		# hmmmm
		resource_food = dictionary.RESOURCES.get(self.resource, {}).get("food", 0)

		if self.worked_by: #this is actually needed otherwise granary bonus applies to all cities
			if any("Granary" in b.name for b in self.worked_by.buildings):
				if self.resource in {"wheat", "deer", "bananas"}:
					resource_food += 1

		if self.owner:
			if self.owner.pantheon == "Sun God":
				if self.resource in {"wheat", "citrus", "bananas"}:
					resource_food += 1

			if self.improvement == "Camp" and self.owner.pantheon == "Goddess of the Hunt":
				resource_food += 1

		if self.improvement == "pasture" and self.resource == "sheep":
			resource_food += 1

		return base_food + resource_food

	@property
	def production(self):
		player = self.owner

		if self.terrain_type == "s":
			base_production = 0
		elif self.trees == 2: # Jungle
			base_production = 0
		elif self.trees == 1: # Forest
			base_production = 1
		elif self.elevation == 1: # Hill with no trees
			base_production = 2
		else:
			base_production = self.terrain_data.get("production", 0)
			
		resource_production = 0
		if self.resource == "horses":
			if player and "Animal Husbandry" in player.science_system.get_unlocked_names():
				resource_production = 1
		elif self.resource == "iron":
			if player and "Iron Working" in player.science_system.get_unlocked_names():
				resource_production = 1
		else:
			# Other resources (like stone or deer) may always provide bonus.... what?
			resource_production = dictionary.RESOURCES.get(self.resource, {}).get("production", 0)

		if self.improvement == "pasture" and (self.resource == "horses" or elf.resource == "cattle" ):
			resource_production += 1

		return base_production + resource_production

	@property
	def gold(self):
		gold = self.terrain_data.get("gold", 0)

		if self.resource:
			gold += dictionary.RESOURCES.get(self.resource, {}).get("gold", 0)

		if self.worked_by and self.resource in {"gold", "silver"}:
			if any("Mint" in b.name for b in self.worked_by.buildings):
				gold += 2

		if self.owner and self.owner.in_golden_age and gold >= 1:
			gold += 1

		return gold

	@property
	def science(self):
		science = self.terrain_data.get("science", 0)
		return science

	@property
	def culture(self):
		culture = self.terrain_data.get("culture", 0)

		if self.improvement == "Plantation" and self.owner:
			player = self.owner
			if "Oral Tradition" in player.unlocked_policies:
				culture += 1

		return culture

	@property
	def faith(self):
		#what about desert folklore?
		if self.resource == "kailash":
			if self.owner.pantheon == "One with Nature":
				return 10
			return 6
		return 0

class Building:
	def __init__(self, name, food=0, production=0, gold=0, maintenance=0, science=0, culture=0, faith =0, happiness=0, growth_percentage=0, production_percentage=0, science_percentage=0, gold_percentage = 0, production_cost=0, gold_cost=0, techs_required=None, policies_required=None, buildings_required=None, wonder=False, national_wonder=False):
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
		self.production_percentage = production_percentage
		self.science_percentage = science_percentage
		self.gold_percentage = gold_percentage

		self.production_cost = production_cost
		self.producable = production_cost > 0
		self.gold_cost = gold_cost
		self.purchasable = gold_cost > 0

		self.techs_required = techs_required or []
		self.policies_required = policies_required or []
		self.buildings_required = buildings_required or []

		self.wonder = wonder
		self.national_wonder = national_wonder
		self.progress = 0 #pass in for free stuff?
		self.completed = False #pass in for free stuff? merge with above 100?

class Unit:
	_id_counter = 0  # class-level variable for unique ID assignment

	def __init__(self, name, player=None, q=None, r=None, hp=100, moves=2, gold_cost=0, production_cost=0, techs_required=None, policies_required=None):
		self.id = Unit._id_counter
		Unit._id_counter += 1 #need to set back to 0 on game start?

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

	def can_move_to(self, from_tile, to_tile):
		if from_tile is None or to_tile is None:
			return False, "Invalid tile (tile does not exist)."
	
		if not helper.in_bounds(to_tile.q, to_tile.r):
			return False, "Target tile is out of bounds."
		
		if self.moves_left == 0:
			return False, "No moves left!"
	
		if helper.hex_distance(from_tile.q, from_tile.r, to_tile.q, to_tile.r) > 1:
			return False, "Can only move to adjacent tiles."
	
		if not to_tile.passable:
			return False, "Impassable tile."
	
		if to_tile.unit is not None:
			return False, "Tile already occupied."
	
		return True, "Valid move."

	def move_to(self, from_tile, to_tile):
		success, message = self.can_move_to(from_tile, to_tile)
		if not success:
			return False, message

		# Calculate movement cost
		move_cost = 1
		if self.name != "Scout":
			if helper.has_river_between(from_tile, to_tile):
				print(f"River detected between ({from_tile.q},{from_tile.r}) and ({to_tile.q},{to_tile.r})")
				move_cost = max(move_cost, 1)
			if to_tile.elevation == 1 or to_tile.trees:
				move_cost = max(move_cost, self.moves_left)  # Use up all moves on rough terrain

		# Apply move
		self.moves_left -= move_cost
		from_tile.unit = None
		to_tile.unit = self
		self.q = to_tile.q
		self.r = to_tile.r

		if to_tile.ancient_ruin:
			ruin = to_tile.ancient_ruin
			ruin.trigger(self.player, to_tile)
			print(f"Ancient Ruins triggered: {ruin.description}")

		return True, "Unit moved successfully."

	def can_improve_tile(self, tile, new_improvement, game):
		if self.name != "Worker":
			return True, "Only Workers can improve tiles."

		if self.moves_left < 1:
			return False, "Not enough movement points to improve."

	def improve_tile(self, tile, improvement, game):
		success, message = can_improve_tile(self, tile, improvement, game)
		
		if not success:
			return success, message
		
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

	def reset_movement(self):
		self.moves_left = self.moves