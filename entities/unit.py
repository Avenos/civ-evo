
#here is unit.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

from data import dictionary, constants
from utils import helper, BoolResult
import math
import heapq
from collections import deque, defaultdict

class Unit:
	_id_counter = 0  # class-level variable for unique ID assignment

	def __init__(self, name, player=None, q=None, r=None, hp=100, moves=2, gold_cost=0, production_cost=0, techs_required=None, policies_required=None, assign_id=True):

		if assign_id:
			self.id = Unit._id_counter
			Unit._id_counter += 1
		else:
			self.id = None  # For unit templates

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
		
		#caravans
		self.route_active = False
		self.route_target = None
		self.route_turns_remaining = 0

	def can_move_to(self, to_tile):
		if to_tile is None:
			return BoolResult(False, "Invalid tile (tile does not exist).")

		if not helper.in_bounds(to_tile.q, to_tile.r):
			return BoolResult(False, "Target tile is out of bounds.")

		if self.moves_left == 0:
			return BoolResult(False, "No moves left!")

		if helper.hex_distance(self.q, self.r, to_tile.q, to_tile.r) != 1:
			return BoolResult(False, "Can only move to adjacent tiles.")

		if not to_tile.passable:
			return BoolResult(False, "Impassable tile.")

		if to_tile.unit is not None:
			return BoolResult(False, "Tile already occupied.")

		return BoolResult(True, "Valid move.")

	def move_to(self, from_tile, to_tile): #easy as this?
		if not (result := self.can_move_to(to_tile)):
			return result

		move_cost = 1
		if self.name != "Scout":
			if helper.has_river_between(from_tile, to_tile):
				move_cost = max(move_cost, 1)
			if to_tile.elevation == 1 or to_tile.trees:
				move_cost = max(move_cost, self.moves_left)

		self.moves_left -= move_cost
		from_tile.unit = None
		to_tile.unit = self
		self.q = to_tile.q
		self.r = to_tile.r

		if to_tile.ancient_ruin:
			ruin = to_tile.ancient_ruin
			ruin.trigger(self.player, to_tile)

		return BoolResult(True, "Unit moved successfully.")

	#to get a LIST of all legal tile improvements do i have to poll every single one...? I guess
	#also roads are a separate thing really...
	def can_improve_tile(self, tile, improvement, game):
		if self.name != "Worker":
			return BoolResult(False, "Only Workers can improve tiles.")
		if self.moves_left < 1:
			return BoolResult(False, "Not enough movement points.")
		if not improvement:
			return BoolResult(False, "No improvement specified.")

		imp_data = dictionary.IMPROVEMENTS.get(improvement)
		if not imp_data:
			return BoolResult(False, f"Unknown improvement '{improvement}'.")

		if "tech_required" in imp_data:
			if not self.player:
				return BoolResult(False, "Player data not found.")
			if imp_data["tech_required"] not in self.player.science_system.unlocked_techs:
				return BoolResult(False, f"{improvement} requires the {imp_data['tech_required']} technology.")

		turns_required = 3 #not sure about this logic

		if "Citizenship" in self.player.unlocked_policies:
			turns_required -= 2

		#we're really checking all cities for this every time...?
		if "Pyramids" in self.player.wonders:
			turns_required -= 2		

		if improvement == tile.improvement and tile.improvement_progress >= turns_required:
			return BoolResult(False, "Improvement already complete!")

		#this is the check def, not the DO def... probably separate chopping at least
		#if improvement == "Road":
			#if tile.road_progress >= turns_required:
				#return False, "Road already complete!"
			#else:
				#tile.road_progress += 1
				#if tile.road_progress >= turns_required:
					#tile.road_complete = True
					#return True, "Road completed!"
				#return True, "Road worked on"

		if tile.owner != self.player:
			return BoolResult(False, "Cannot improve tile you do not own.") #unless its a road

		elif improvement == "Farm":
			if tile.resource not in ["wheat", "n"]: #...does wheat override everthing except trees? how to code that?
				return BoolResult(False, "Not a valid resource for farms") # how does this work before we discover iron and horses?
			elif tile.trees != 0:
				return BoolResult(False, "Need to remove trees first")
			elif tile.terrain_type == "t" and not tile.fresh_water: #this is logically wrong, need an OR statement for tundra
				return BoolResult(False, "Need fresh water to build farm on tundra")
			elif tile.terrain_type not in ["g", "p", "d"]:
				return BoolResult(False, "Cannot build farm on this terrain")
			elif tile.elevation == 1 and not tile.fresh_water:
				return BoolResult(False, "Need fresh water to build farm on hill")
			else:
				return BoolResult(True, "Can build farm")

		elif improvement == "Mine":
			if tile.trees != 0:
				return BoolResult(False, "Need to remove trees first")		
			elif tile.resource not in ["iron", "salt", "copper", "gems", "gold", "silver", "n"]:
				return BoolResult(False, "Cannot build mine unless it is on a hill or has a valid resource")
			elif tile.elevation != 1:
				return BoolResult(False, "Cannot build a mine on flat land with no resource")
			else:
				return BoolResult(True, "Can build mine")

		elif improvement == "Pasture":
			if tile.trees != 0:
				return BoolResult(False, "Need to remove trees first")		
			elif tile.resource not in ["cattle", "sheep", "horses"]:
				return BoolResult(False, "Cannot build pasture without cattle, sheep, or horses")
			else:
				return BoolResult(True, "Can build pasture")

		elif improvement == "Plantation":
			if tile.trees != 0:
				return BoolResult(False, "Need to remove trees first")	
			elif tile.resource not in ["citrus", "dyes", "cotton", "incense", "spices", "sugar", "bananas", "silk"]:
				return BoolResult(False, "Not a valid resource")
			else:
				return BoolResult(True, "Can build plantation")

		elif improvement == "Quarry":
			if tile.trees != 0:
				return BoolResult(False, "Need to remove trees first")			
			elif tile.resource not in ["stone", "marble"]:
				return BoolResult(False, "Not a valid resource")
			else:
				return BoolResult(True, "Can build quarry")

		elif improvement == "Camp": #chopping would remove the camp?			
			if tile.resource not in ["ivory", "truffles", "deer", "bison", "furs"]:
				return BoolResult(False, "Not a valid resource")
			else:
				return BoolResult(True, "Can build quarry")	

		elif improvement == "Trading Post":
			if tile.terrain_type not in ["g", "p", "d", "t"]:
				return BoolResult(False, "Not a valid terrain type")
			else:
				return BoolResult(True, "Can build trading post")
		
		else:
			return BoolResult(False, "Something went wrong")	

	def improve_tile(self, tile, improvement, game):
		if not (result := self.can_improve_tile(tile, improvement, game)):
			return result

		if tile.improvement != improvement:
			tile.improvement = improvement
			tile.improvement_progress = 0

		turns_required = 3 #not sure about this logic

		if "Citizenship" in self.player.unlocked_policies:
			turns_required -= 2

		if "Pyramids" in self.player.wonders:
			turns_required -= 2

		tile.improvement_progress += 1
		self.moves_left = 0

		if tile.improvement_progress < turns_required:
			return BoolResult(True, "Improvement worked on.")

		if tile.improvement_progress >= turns_required:
			tile.improvement_complete = True

			#need to check that its the right improvement though... otherwise farms can wire up luxes
			if dictionary.RESOURCES.get(tile.resource, {}).get("luxury", False):
				self.player.luxuries.append(tile.resource)
			
			return BoolResult(True, f"{improvement} completed!")

	def can_establish_trade_route(self, dest_city, engine):
		player = self.owner
		
		if self.name != "Caravan":
			return BoolResult(False, "Only Caravans can establish trade routes.")
	
		if not self.tile.city:
			return BoolResult(False, "Caravan must be stationed in a city.")
	
		if not self.tile.city.has_granary:
			return BoolResult(False, "Trade routes require a Granary in the origin city.")
	
		if dest_city == self.tile.city:
			return BoolResult(False, "Cannot establish a trade route to the same city.")
	
		if len(player.active_trade_routes) >= player.max_trade_routes:
			return BoolResult(False, "Maximum number of trade routes reached.")
	
		if self.route_active:
			return BoolResult(False, "This Caravan is already assigned to a trade route.")
	
		# Optionally: check if destination is a valid target (same player?)
		if dest_city.owner != player:
			return BoolResult(False, "Can only trade with your own cities (for now).")
	
		return BoolResult(True, "Can establish trade route")
	
	def establish_trade_route(self, dest_city, engine):
		if not (result := self.can_establish_trade_route(dest_city, engine)):
			return result
	
		self.route_active = True
		self.route_target = dest_city
		self.route_turns_remaining = 30
		self.has_moved = True
	
		self.owner.active_trade_routes.append({
			"unit_id": self.id,
			"from": self.tile.city.id,
			"to": dest_city.id,
			"turns": 30
		})
	
		return BoolResult(True, f"Established trade route to {dest_city.name} for 30 turns.")

	def can_rebase(self, city):
		if self.name != "Caravan":
			return BoolResult(False, "Only Caravans can rebase.")
	
		if not city in self.owner.cities:
			return BoolResult(False, "Can only rebase to own cities.")
	
		if city == self.tile.city:
			return BoolResult(False, "Already based in this city.")
	
		return BoolResult(True, "Can rebase")
	
	def rebase_to(self, city):
		if not (result := self.can_rebase(city)):
			return result
	
		# We'll simulate "rebasing" by teleporting the unit
		self.q, self.r = city.q, city.r
		self.route_active = False
		self.route_target = None
		self.route_turns_remaining = 0
	
		return BoolResult(True, f"Rebased to {city.name}.")

	def reset_movement(self):
		self.moves_left = self.moves
