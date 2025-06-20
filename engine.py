
import json
import helper
import constants
import dictionary
from core import Tile, Unit
from player import Player
from constants import GRID_HEIGHT, GRID_WIDTH

class Engine:
	def __init__(self):
		self.is_replay = False  # Set True during replay
		self.recorded_actions = []  # Populated only during manual play		
		
		self.message = ""
		self.message_timer = 0
		self.action_log = {}

		with open("map.json") as f:
			map_layout = json.load(f)

		self.tiles = []
		self.units = []

		transposed_layout = list(zip(*map_layout))  # transpose rows/cols

		for q, col in enumerate(transposed_layout):  # q = vertical (cols)
			tile_col = []
			for r, tile_data in enumerate(col):       # r = horizontal (rows)
				terrain, elevation, trees, resource = tile_data
				tile = Tile(q, r, terrain, elevation, trees, resource)
				tile_col.append(tile)
			self.tiles.append(tile_col)

		helper.add_river(self.tiles[2][2], 0, self.tiles)
		helper.add_river(self.tiles[3][3], 0, self.tiles)
		helper.add_river(self.tiles[4][4], 0, self.tiles)
		helper.add_river(self.tiles[5][5], 0, self.tiles)
		helper.add_river(self.tiles[3][4], 1, self.tiles)
		helper.add_river(self.tiles[3][4], 0, self.tiles)
		helper.add_river(self.tiles[2][5], 0, self.tiles)

		for q in range(GRID_WIDTH):
			for r in range(GRID_HEIGHT):
				if self.tiles[q][r].rivers:
					print(f"Tile ({q},{r}) rivers: {sorted(self.tiles[q][r].rivers)}")


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

		self.turn = 1

		self.ui_found_city_button = None
		self.ui_next_turn_button = None		
		self.all_policies = helper.build_policy_objects(dictionary.POLICIES)
		self.ui_policy_buttons = []
		self.ui_purchase_buttons = []
		self.ui_production_buttons = []
		self.ui_pantheon_buttons = []
		self.taken_pantheons = []
		self.all_pantheons = dictionary.PANTHEONS

		#city state reward
		self.special_tiles = [(15, 3)]  # Replace with your actual tile coordinates
		self.tile_rewards_claimed = {}  # key: (q, r), value: set of player IDs who already claimed it		

		self.territory = set()

		self.players = [Player()]
		self.current_player = self.players[0]

		self.spawn_unit(self.players[0], 6, 8, "Worker")
		self.spawn_unit(self.players[0], 7, 8, "Settler")
		self.spawn_unit(self.players[0], 8, 8, "Warrior")

		self.selected_unit = None
		self.selected_city = None
		
	def evaluate_result(self):
		total_science = self.engine.currentplayer.total_science_accrued  # Accumulate this in your engine
		total_pop = sum(city.population for city in self.engine.cities)
		return total_science + 50 * total_pop

	def record_action(self, turn, action_type, data):
		if not self.is_replay:
			engine.recorded_actions.append([turn, action_type, data])
			
	def get_legal_actions(self, player):
		actions = []
	
		# Move units
		for unit in player.units:
			for dq, dr in directions:  # probably 6 hex directions
				to_q = unit.q + dq
				to_r = unit.r + dr
				if self.can_move_unit(unit, to_q, to_r):  # <- YOUR check
					actions.append({"action": "move_unit", "unit_id": unit.id, "to": [to_q, to_r]})
	
		# Found city
		for unit in player.units:
			if unit.name == "Settler" and self.can_found_city(unit):  # <- YOUR logic
				actions.append({"action": "found_city", "unit_id": unit.id})
	
		# Policy selection
		if player.can_choose_policy():
			for policy in player.get_available_policies():
				actions.append({"action": "select_policy", "policy": policy})
	
		# Tech selection
		if player.science_system.needs_research():
			for tech in player.science_system.get_available_techs():
				actions.append({"action": "select_tech", "tech": tech})
	
		# City production
		for city in player.cities:
			if city.needs_production():
				for buildable in city.get_buildable_things():
					actions.append({"action": "set_production", "city_id": city.id, "name": buildable})
	
		# End turn (only if all required actions are taken)
		if self.can_end_turn(player):
			actions.append({"action": "end_turn"})
	
		return actions	

	def show_message(self, text, duration=90):
		self.message = text
		self.message_timer = duration

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
			with open("replayX.json", "w") as f:
				json.dump(self.action_log, f, indent=2)			
			return True
		else:
			print(f"Turn error: {message}")
			self.show_message(message, 180)
	
			return False

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
			    "name": self.name,
				"gold": self.gold,
			    "culture": self.culture,
				"science": self.science,
				"faith": self.faith,
				"unlocked_policies": list(self.unlocked_policies),
				"current_research": self.science_system.current_research,
				},
		    "units": [
				{
					"type": u.name,
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
					"worked_tiles": list(c.worked_tiles),
					"build_queue": c.build_queue[:],  # if applicable
					"build_progress": c.build_progress,
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
						"gold": t.gold,
						"city": t.city.name if t.city else None,
						"improvement": t.improvement,
						"unit": t.unit.name if t.unit else None,
						"territory": t.territory,
				    }
				    for t in col
				]
				for col in self.tiles
			    ],
		}