
#here is engine.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import json
from utils import helper
from data import constants, dictionary

from entities import Tile, Unit, City, Player, AncientRuins
from engine import action_handler

class EnvWrapper:
	def __init__(self):
		self.engine = Engine()

	def reset(self):
		self.engine.reset_game()
		return self.engine.get_state()

	def step(self, action):
		# Action is a dict like {"action": ..., "data": {...}}
		success, error = action_handler.handle_action(self.engine, action["action"], action.get("data", {}))

		# Calculate reward (you must define your reward logic here)
		# Example: reward = current_population + current_science (or whatever you want)
		current_player = self.engine.current_player
		reward = 50 * sum(city.population for city in current_player.cities) + getattr(current_player, "total_science_accrued", 0)

		# Check if episode done, e.g. after fixed turns or game over condition
		done = self.engine.turn >= 40  # example stopping condition

		# Optionally include error info or other info
		info = {"success": success, "error": error}

		next_state = self.engine.get_state()

		return next_state, reward, done, info

class Engine:
	def __init__(self):
		self.reset_game()

	def reset_game(self):
		Unit._id_counter = 0
		City._id_counter = 0

		self.record_actions = False
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

		for q, col in enumerate(transposed_layout):
			tile_col = []
			for r, tile_data in enumerate(col):
				terrain, elevation, trees, resource = tile_data
				tile = Tile(q, r, terrain, elevation, trees, resource)
				tile_col.append(tile)
			self.tiles.append(tile_col)

		helper.assign_fresh_water_flags(self)

		self.ui_found_city_button = None
		self.ui_next_turn_button = None
		self.ui_tech_buttons = []
		self.ui_policy_buttons = []
		self.ui_purchase_buttons = []
		self.ui_production_buttons = []
		self.ui_pantheon_buttons = []
		self.ui_tile_improvement_buttons = []

		self.all_policies = helper.build_policy_objects(dictionary.POLICIES)
		self.all_pantheons = dictionary.PANTHEONS
		self.taken_pantheons = []

		#self.city_states = [(15, 3)]
		#self.city_states_met = {} #[]?

		self.players = [Player()]
		self.current_player = self.players[0]
		self.replay_log_filepath = None

		self.spawn_unit(self.players[0], "Worker", 10, 8)
		self.spawn_unit(self.players[0], "Settler", 11, 8)
		self.spawn_unit(self.players[0], "Warrior", 12, 8)

		self.tiles[6][6].ancient_ruin = AncientRuins(2)

		self.selected_unit = None
		self.selected_city = None

	def show_message(self, text, duration=90):
		self.message = text
		self.message_timer = duration

	def spawn_unit(self, player, name, q, r): #this is not entirely accurate
		tile = self.get_tile(q, r)

		if tile.unit is None:
			unit = Unit(name, player, q, r)
			self.units.append(unit)
			player.units.append(unit)
			self.tiles[q][r].unit = unit
			return True, "Unit spawned"
		else:
			for nq, nr in hex_neighbors(q, r):
				tile = game.tiles[nq][nr]
				if tile.unit is None:
					unit = Unit(name, player, q, r)
					self.units.append(unit)
					player.units.append(unit)
					self.tiles[q][r].unit = unit
					return True, "Unit spawned on neighboring tile"
		return False, "No room to spawn unit!"

	def remove_unit(self, unit):
		self.units = [u for u in self.units if u.id != unit.id]
		if unit.player:
			unit.player.units = [u for u in unit.player.units if u.id != unit.id]
		tile = self.get_tile(unit.q, unit.r)
		if tile and tile.unit and tile.unit.id == unit.id:
			tile.unit = None

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

	def get_tile(self, q, r):
		return self.tiles[q][r]

	def get_unit_at(self, q, r):
		return self.tiles[q][r].unit

	def get_city_at(self, q, r):
		return self.tiles[q][r].city

	def end_turn(self):
		self.turn += 1
		self.selected_unit = None
		
		for unit in self.current_player.units:
			if unit.name == "Caravan" and unit.route_active:
				unit.route_turns_remaining -= 1
				if unit.route_turns_remaining <= 0:
					unit.route_active = False
					unit.route_target = None
		
				else:
					# Apply effects every turn — e.g., +4 food to target city
					unit.route_target.food_storage += 4
		
		
		self.start_turn()
		return True

	def start_turn(self):
		for city in self.current_player.cities:
			city.production_system.apply_production(self)

	def get_legal_actions(self, player):
		actions = []

		for unit in player.units:
			for dq, dr in helper.hex_neighbors(unit.q, unit.r):
				to_tile = self.get_tile(dq, dr)
				if unit.can_move_to(to_tile)[0]:
					actions.append({"action": "move_unit", "data": {"unit_id": unit.id, "to": [dq, dr]}})

		for unit in player.units:
			if player.can_found_city(unit, self)[0]:
				actions.append({"action": "found_city", "data": {"unit_id": unit.id}})

		for unit in player.units:
			if unit.name == "Worker":
				tile = self.get_tile(unit.q, unit.r)
				for improvement_name in dictionary.IMPROVEMENTS.keys():
					if improvement_name in ["Road", "None"]:
						continue  # Skip non-improvement types here if needed
					success, _ = unit.can_improve_tile(tile, improvement_name, self)
					if success:
						actions.append({
							"action": "improve_tile",
							"data": {
								"unit_id": unit.id,
								"tile_coords": (tile.q, tile.r),
								"improvement": improvement_name
							}
						})

		#all policies already researched check? also....this should only check at the BEGINNING of a turn... not during...
		if self.current_player.culture < self.current_player.policy_cost:
			for policy_name in self.all_policies:
				if player.can_choose_policy(policy_name, self)[0]:
					actions.append({"action": "choose_policy", "data": {"policy_name": policy_name}})

		if not player.science_system.current_research: #disallow swapping, its pointless - except for that minor civil service exploit
			for tech in player.science_system.get_available_techs():
				actions.append({"action": "choose_research", "data": {"tech_name": tech}})

		if player.can_choose_pantheon()[0]:
			for pantheon in self.all_pantheons:
				actions.append({"action": "choose_pantheon", "data": {"pantheon": pantheon}})

		for city in player.cities:
			if not city.production_system.current_project: #disallow production swapping for now?
				for project in city.production_system.get_available_projects():
					actions.append({"action": "choose_project", "data": {"city_id": city.id, "project_name": project.name}})

		for city in player.cities:
			for tile in city.get_purchasable_tiles(self):
				actions.append({"action": "purchase_tile", "data": {"city_id": city.id, "tile_coords": (tile.q, tile.r)}})

		for city in player.cities:
			for building in city.production_system.building_projects:
				can_purchase, _ = city.can_purchase_building(building.name, player)
				if can_purchase:
					actions.append({
						"action": "purchase_building",
						"data": {
							"city_id": city.id,
							"name": building.name
						}
					})

			for unit in city.production_system.unit_projects:
				can_purchase, _ = city.can_purchase_unit(unit.name, player)
				if can_purchase:
					actions.append({
						"action": "purchase_unit",
						"data": {
							"city_id": city.id,
							"name": unit.name
						}
					})

		for city in player.cities:
			# UNASSIGN worked tiles
			for tile in city.worked_tiles:
				actions.append({
					"action": "unassign_tile",
					"data": {"city_id": city.id, "tile": (tile.q, tile.r)}
				})
		
			# ASSIGN new workable tiles if city has spare citizens
			if len(city.worked_tiles) < city.population:
				workable_tiles = city.get_workable_tiles(self)
				for tile in workable_tiles:
					if tile not in city.worked_tiles:
						actions.append({
							"action": "assign_tile",
							"data": {"city_id": city.id, "tile": (tile.q, tile.r)}
						})

		for unit in player.units:
			if unit.name == "Caravan" and not unit.route_active:
				if unit.tile.city and unit.tile.city.has_granary:
					for dest in player.cities:
						if dest != unit.tile.city:
							success, _ = unit.can_establish_trade_route(dest, self)
							if success:
								actions.append({
									"action": "establish_trade_route",
									"data": {
										"unit_id": unit.id,
										"dest_city_id": dest.id
									}
								})
								
		# rebase options
		for city in player.cities:
			tile = self.get_tile(city.q, city.r)
			if city != tile.city:
				success, _ = unit.can_rebase(city)
				if success:
					actions.append({
						"action": "rebase_caravan",
						"data": {
							"unit_id": unit.id,
							"dest_city_id": city.id
						}
					})

		if player.can_end_turn()[0]:
			actions.append({"action": "end_turn", "data": {}})

		return actions

	def get_state(self):
		return {
			"turn": self.turn,
			"player": {
				"total_science_accrued": self.current_player.total_science_accrued,
				"science_per_turn": self.current_player.science_per_turn,				
				"gold": self.current_player.gold,
				"gold_per_turn": self.current_player.gold_per_turn,
				"culture": self.current_player.culture,
				"culture_per_turn": self.current_player.culture_per_turn,
				"faith": self.current_player.faith,
				"faith_per_turn": self.current_player.faith_per_turn,
				"pantheon": self.current_player.pantheon,
				"happiness": self.current_player.happiness,
				"luxuries": self.current_player.luxuries,
				"unlocked_policies": self.current_player.unlocked_policies,
				"unlocked_techs": self.current_player.science_system.unlocked_techs,
				"current_research": self.current_player.science_system.current_research,
				"current_research_progress": self.current_player.science_system.current_research_progress,
				"era": self.current_player.era,
				"golden_age_turns_left": self.current_player.golden_age_turns_left,
				"trade_routes": self.current_player.trade_routes,
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
					"production": c.production_per_turn,
					"science": c.science,
					"culture": c.culture,
					"faith": c.faith,
					"worked_tiles": c.worked_tiles,
					"current_production": c.production_system.current_project,
					#building list?
				}
				for c in self.current_player.cities
				],
			"tiles": [
				[
					{
						"q": t.q,
						"r": t.r,
						"terrain_type": t.terrain_type,
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
