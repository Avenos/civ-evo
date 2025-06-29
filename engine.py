
import json
import helper
import constants
import dictionary
from core import Tile, Unit
from player import Player
from constants import GRID_HEIGHT, GRID_WIDTH

class Engine:
	def __init__(self):
		self.is_replay = False
		self.recorded_actions = []

		self.message = ""
		self.message_timer = 0
		self.action_log = {}

		self.turn = 1
		self.tiles = []
		self.units = []

		with open("maps//indianSubcontinent.json") as f:
			map_layout = json.load(f)

		transposed_layout = list(zip(*map_layout))

		for q, col in enumerate(transposed_layout):  # q = columns
			tile_col = []
			for r, tile_data in enumerate(col):  # r = rows
				terrain, elevation, trees, resource = tile_data
				tile = Tile(q, r, terrain, elevation, trees, resource)
				tile_col.append(tile)
			self.tiles.append(tile_col)

		# --- A* TEST BLOCK --- #
		#print("\nRunning pathfinding test...")

		## Convert self.tiles into flat game_map dict {(q,r): Tile}
		#game_map = {}
		#for col in self.tiles:
			#for tile in col:
				#game_map[(tile.q, tile.r)] = tile

		#start = (0, 1)
		#goal = (5, 5)
		#move_points_per_turn = 2

		#path = helper.a_star_path(start, goal, game_map, move_points_per_turn)

		self.ui_found_city_button = None
		self.ui_next_turn_button = None		
		self.all_policies = helper.build_policy_objects(dictionary.POLICIES)
		self.ui_policy_buttons = []
		self.ui_purchase_buttons = []
		self.ui_production_buttons = []
		self.ui_pantheon_buttons = []
		self.taken_pantheons = []
		self.all_pantheons = dictionary.PANTHEONS

		self.city_states = [(15, 3)]
		self.city_states_met = {}  # key: (q, r), value: set of player IDs who already claimed it
		self.players = [Player()]
		self.current_player = self.players[0]

		self.spawn_unit(self.players[0], 8, 8, "Worker")
		self.spawn_unit(self.players[0], 9, 8, "Settler")
		self.spawn_unit(self.players[0], 10, 8, "Warrior")

		self.selected_unit = None
		self.selected_city = None

	def record_action(self, turn, action_type, data):
		if not self.is_replay:
			engine.recorded_actions.append([turn, action_type, data])

	def get_legal_actions(self, player):
		actions = []

		# Move units
		for unit in player.units:
			for dq, dr in helper.hex_neighbors(unit.q, unit.r):
				to_q = unit.q + dq
				to_r = unit.r + dr
				if unit.can_move_unit(unit, to_q, to_r):
					actions.append({"action": "move_unit", "unit_id": unit.id, "to": [to_q, to_r]})

		# Found city, improve tiles, assign trade route
		for unit in player.units:
			if unit.name == "Settler" and self.can_found_city(unit):
				actions.append({"action": "found_city", "unit_id": unit.id})
			if unit.name == "Worker" and self.can_improve_tile(unit):
				actions.append({"action": "improve_tile", "unit_id": unit.id})				
			if unit.name == "Caravan":
				for city in player.cities:
					if self.can_assign_trade_route(unit, city): #check for granary and distance
						actions.append({"action": "assign trade route", "unit_id": unit.id, "city_id": city.id})				

		# Policy selection
		if player.can_choose_policy():
			for policy in player.get_available_policies():
				actions.append({"action": "select_policy", "policy": policy})

		# Tech selection
		if player.science_system.needs_research():
			for tech in player.science_system.get_available_techs():
				actions.append({"action": "select_tech", "tech": tech})

		# Pantheon selection
		if player.can_choose_pantheon():
			for pantheon in player.available_panethonds():
				actions.append({"action": "select_pantheon", "pantheon": pantheon})

		# City production
		for city in player.cities:
			if city.needs_production(): #restrict production swapping or no?
				for buildable in city.get_buildable_things():
					actions.append({"action": "set_production", "city_id": city.id, "name": buildable})

		# City purchasing
		for city in player.cities:
			if city.needs_production(): #restrict production swapping or no?
				for buildable in city.get_buildable_things():
					actions.append({"action": "set_production", "city_id": city.id, "name": buildable})

		# Tile purchasing
		#for city in player.cities:
			#for every tile in the cities radius, check if can_buy_tile, if so add it to the list

		# Assign worked tile

		# Unassign worked tile

		# End turn (this should probably be an action yeah?)
		if self.can_end_turn(player):
			actions.append({"action": "end_turn"})

		return actions	

	def show_message(self, text, duration=90):
		self.message = text
		self.message_timer = duration

	#should this be in helper.py?
	def spawn_unit(self, player, q, r, name):
		unit = Unit(name, player=player, q=q, r=r)
		self.units.append(unit)
		self.tiles[q][r].unit = unit
		return unit

	def get_unit_by_id(self, unit_id):
		for unit in self.units:
			if unit.id == unit_id:
				return unit
		return None

	def get_city_by_id(self, city_id):
		for player in self.players:
			for city in player.cities:
				if city.id == city_id:
					return city
		return None

	def get_unit_at(self, q, r):
		return self.tiles[q][r].unit

	def get_city_at(self, q, r):
		return self.tiles[q][r].city

	# For events processed at the START of a turn
	def start_turn(self):
		for city in self.current_player.cities:
			city.production_system.apply_production(self)

	def end_turn(self):
		success, message = self.current_player.end_turn(self)

		if success:
			self.turn += 1
			self.selected_unit = None
			self.spawn_worker_on_schedule()
			self.start_turn()		
			return True
		else:
			print(f"Turn error: {message}")
			self.show_message(message, 180)

			return False

	#helper method?
	def spawn_worker_on_schedule(self, start_turn=20, interval=10, spawn_tile_q=0, spawn_tile_r=0):
		if self.turn >= start_turn and (self.turn - start_turn) % interval == 0:
			tiles_map = self.tiles

			q, r = spawn_tile_q, spawn_tile_r
			width = len(tiles_map)
			height = len(tiles_map[0])

			checked_positions = set()

			while (q, r) not in checked_positions:
				checked_positions.add((q, r))
				tile = tiles_map[q][r]
				if tile.unit is None:
					# Spawn worker unit here
					new_worker = Unit("Worker", self.current_player, q, r)
					self.units.append(new_worker)
					self.current_player.units.append(new_worker)
					tile.unit = new_worker
					break

				# Move to next tile in row-major order
				q += 1
				if q >= width:
					q = 0
					r += 1
					if r >= height:
						r = 0

	def get_tile(self, q, r):
		return self.tiles[q][r]

	def get_state(self):
		return {
			"turn": self.turn,
			"player": {
				"name": self.current_player.name,
				"gold": self.current_player.gold,
				"gold_per_turn": self.current_player.gold_per_turn,
				"culture": self.current_player.culture,
				"culture_per_turn": self.current_player.culture_per_turn,
				"science": self.current_player.science,
				"science_per_turn": self.current_player.science_per_turn,
				"faith": self.current_player.faith,
				"faith_per_turn": self.current_player.faith_per_turn,
				"pantheon": self.current_player.pantheon,
				"luxuries": self.current_player.luxuries,
				"unlocked_policies": self.unlocked_policies,
				"unlocked_techs": self.current_player.science_system.unlocked_techs,
				"current_research": self.current_player.science_system.current_research,
				"current_research_progress": self.current_player.current_research.progress
				},
			"units": [
				{
					"name": u.name,
					"q": u.q,
					"r": u.r,
					"moves_left": u.moves_left,
				}
				for u in self.units
				],
			"cities": [
				{
					"name": c.name,
					"q": c.q,
					"r": c.r,
					"population": c.population,
					"food": c.food,
					"production": c.production,
					"science": c.science,
					"culture": c.culture,
					"faith": c.faith,
					"worked_tiles": c.worked_tiles,
					"current_production": c.production_system.current_project,
					"current_production_progress": c.production_system.current_project.progress,
				}
				for c in self.cities
				],
			"tiles": [
				[
					{
						"q": t.q,
						"r": t.r,
						"terrain": t.terrain,
						"elevation": t.elevation,
						"trees": t.trees,
						"resource": t.resource,
						"food": t.food,
						"production": t.production,
						"science": t.science,
						"gold": t.gold,
						"culture": t.culture,						
						"faith": t.faith,			
						"improvement": t.improvement,
						"city": t.city.name if t.city else None,
						"unit": t.unit.name if t.unit else None,
						"owner": t.owner,
					}
					for t in col
				]
				for col in self.tiles
				],
		}