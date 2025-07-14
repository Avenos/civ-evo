
#here is unit.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

from data import dictionary, constants
from utils import helper
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

	def can_move_to(self, to_tile):
		if to_tile is None:
			return False, "Invalid tile (tile does not exist)."

		if not helper.in_bounds(to_tile.q, to_tile.r):
			return False, "Target tile is out of bounds."

		if self.moves_left == 0:
			return False, "No moves left!"

		if helper.hex_distance(self.q, self.r, to_tile.q, to_tile.r) != 1:
			return False, "Can only move to adjacent tiles."

		if not to_tile.passable:
			return False, "Impassable tile."

		if to_tile.unit is not None:
			return False, "Tile already occupied."

		return True, "Valid move."

	def move_to(self, from_tile, to_tile, verified=False): #easy as this?
		if not verified:
			success, message = self.can_move_to(to_tile)
			if not success:
				return False, message

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

		return True, "Unit moved successfully."

	#to get a LIST of all legal tile improvements do i have to poll every single one...? I guess
	#also roads are a separate thing really...
	def can_improve_tile(self, tile, improvement, game):
		if self.name != "Worker":
			return False, "Only Workers can improve tiles."
		if self.moves_left < 1:
			return False, "Not enough movement points."
		if not improvement:
			return False, "No improvement specified."

		imp_data = dictionary.IMPROVEMENTS.get(improvement)
		if not imp_data:
			return False, f"Unknown improvement '{improvement}'."

		if "tech_required" in imp_data:
			if not self.player:
				return False, "Player data not found."
			if imp_data["tech_required"] not in self.player.science_system.unlocked_techs:
				return False, f"{improvement} requires the {imp_data['tech_required']} technology."

		turns_required = 3 #not sure about this logic

		if "Citizenship" in self.player.unlocked_policies:
			turns_required -= 2

		#we're really checking all cities for this every time...?
		if "Pyramids" in self.player.wonders:
			turns_required -= 2		

		if improvement == tile.improvement and tile.improvement_progress >= turns_required:
			return False, "Improvement already complete!"

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
			return False, "Cannot improve tile you do not own." #unless its a road

		elif improvement == "Farm":
			if tile.resource not in ["wheat", "n"]: #...does wheat override everthing except trees? how to code that?
				return False, "Not a valid resource for farms" # how does this work before we discover iron and horses?
			elif tile.trees != 0:
				return False, "Need to remove trees first"
			elif tile.terrain_type == "t" and not tile.fresh_water: #this is logically wrong, need an OR statement for tundra
				return False, "Need fresh water to build farm on tundra"
			elif tile.terrain_type not in ["g", "p", "d"]:
				return False, "Cannot build farm on this terrain"
			elif tile.elevation == 1 and not tile.fresh_water:
				return False, "Need fresh water to build farm on hill"	
			else:
				return True, "Can build farm"

		elif improvement == "Mine":
			if tile.trees != 0:
				return False, "Need to remove trees first"			
			elif tile.resource not in ["iron", "salt", "copper", "gems", "gold", "silver", "n"]:
				return False, "Cannot build mine unless it is on a hill or has a valid resource"
			elif tile.elevation != 1:
				return False, "Cannot build a mine on flat land with no resource"
			else:
				return True, "Can build mine"

		elif improvement == "Pasture":
			if tile.trees != 0:
				return False, "Need to remove trees first"			
			elif tile.resource not in ["cattle", "sheep", "horses"]:
				return False, "Cannot build pasture without cattle, sheep, or horses"
			else:
				return True, "Can build pasture"

		elif improvement == "Plantation":
			if tile.trees != 0:
				return False, "Need to remove trees first"			
			elif tile.resource not in ["citrus", "dyes", "cotton", "incense", "spices", "sugar", "bananas", "silk"]:
				return False, "Not a valid resource"
			else:
				return True, "Can build plantation"

		elif improvement == "Quarry":
			if tile.trees != 0:
				return False, "Need to remove trees first"			
			elif tile.resource not in ["stone", "marble"]:
				return False, "Not a valid resource"
			else:
				return True, "Can build quarry"

		elif improvement == "Camp": #chopping would remove the camp?			
			if tile.resource not in ["ivory", "truffles", "deer", "bison", "furs"]:
				return False, "Not a valid resource"
			else:
				return True, "Can build quarry"		

		elif improvement == "Trading Post":
			if tile.terrain_type not in ["g", "p", "d", "t"]:
				return False, "Not a valid terrain type"
			else:
				return True, "Can build trading post"

	def improve_tile(self, tile, improvement, game):
		success, message = self.can_improve_tile(tile, improvement, game)
		if not success:
			return False, message

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
			return True, "Improvement worked on."

		if tile.improvement_progress >= turns_required:
			tile.improvement_complete = True

			#need to check that its the right improvement though... otherwise farms can wire up luxes
			if dictionary.RESOURCES.get(tile.resource, {}).get("luxury", False):
				self.player.luxuries.append(tile.resource)
			
			return True, f"{improvement} completed!"

	def can_establish_trade_route(self, dest_city, engine):
		player = self.owner
		
		if self.name != "Caravan":
			return False, "Only Caravans can establish trade routes."
	
		if not self.tile.city:
			return False, "Caravan must be stationed in a city."
	
		if not self.tile.city.has_granary:
			return False, "Trade routes require a Granary in the origin city."
	
		if dest_city == self.tile.city:
			return False, "Cannot establish a trade route to the same city."
	
		if len(player.active_trade_routes) >= player.max_trade_routes:
			return False, "Maximum number of trade routes reached."
	
		if self.route_active:
			return False, "This Caravan is already assigned to a trade route."
	
		# Optionally: check if destination is a valid target (same player?)
		if dest_city.owner != player:
			return False, "Can only trade with your own cities (for now)."
	
		return True, "Can establish trade route"
	
	def establish_trade_route(self, dest_city, engine):
		success, msg = self.can_establish_trade_route(dest_city, engine)
		if not success:
			return success, msg
	
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
	
		return True, f"Established trade route to {dest_city.name} for 30 turns."

	def can_rebase(self, city):
		if self.name != "Caravan":
			return False, "Only Caravans can rebase."
	
		if not city in self.owner.cities:
			return False, "Can only rebase to own cities."
	
		if city == self.tile.city:
			return False, "Already based in this city."
	
		return True, "Can rebase"
	
	def rebase_to(self, city):
		success, msg = self.can_rebase(city)
		if not success:
			return False, msg
	
		# We'll simulate "rebasing" by teleporting the unit
		self.q, self.r = city.q, city.r
		self.has_moved = True
		self.route_active = False
		self.route_target = None
		self.route_turns_remaining = 0
	
		return True, f"Rebased to {city.name}."


	def reset_movement(self):
		self.moves_left = self.moves
