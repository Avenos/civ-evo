
from data import dictionary, constants
from utils import helper
import math
import heapq
from collections import deque, defaultdict

class Unit:
	_id_counter = 0  # class-level variable for unique ID assignment

	def __init__(self, name, player=None, q=None, r=None, hp=100, moves=2,
		     gold_cost=0, production_cost=0, techs_required=None,
		     policies_required=None, assign_id=True):

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


	def can_move_to(self, to_tile):
		if to_tile is None:
			return False, "Invalid tile (tile does not exist)."

		if not helper.in_bounds(to_tile.q, to_tile.r):
			return False, "Target tile is out of bounds."

		if self.moves_left == 0:
			return False, "No moves left!"

		#this could use the neighbors method?
		if helper.hex_distance(self.q, self.r, to_tile.q, to_tile.r) != 1:
			return False, "Can only move to adjacent tiles."

		if not to_tile.passable:
			return False, "Impassable tile."

		if to_tile.unit is not None:
			return False, "Tile already occupied."

		return True, "Valid move."

	def move_to(self, from_tile, to_tile):
		success, message = self.can_move_to(to_tile)
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
		if tile.terrain not in imp_data["allowed_terrains"]:
			return False, f"Cannot build {improvement} on {tile.terrain}."
		return True, ""

	def improve_tile(self, tile, improvement, game):
		success, msg = self.can_improve_tile(tile, improvement, game)
		if not success:
			return False, msg
	
		if tile.improvement != improvement:
			# New improvement requested
			tile.improvement = improvement
			tile.improvement_progress = 0
	
		tile.improvement_progress += 1
		self.moves_left -= 1
	
		imp_data = dictionary.IMPROVEMENTS[improvement]
		if tile.improvement_progress >= imp_data["turns_required"]:
			tile.improvement_progress = imp_data["turns_required"]
			if game:
				game.show_message(f"{improvement.capitalize()} completed on tile ({tile.q}, {tile.r})!", 90)
			return True, f"{improvement} completed!"
	
		return False, f"{improvement} in progress ({tile.improvement_progress}/{imp_data['turns_required']})"


	def reset_movement(self):
		self.moves_left = self.moves