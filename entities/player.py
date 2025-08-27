
#here is player.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

from data import dictionary, constants
from . import City
from utils import helper, BoolResult
from systems import ScienceSystem

import math
from collections import Counter

class Player:
	def __init__(self, name="Avenos"):
		self.name = name
		self.units = []
		self.cities = []
		self.luxuries = []
		self.improved_tiles = []
		self.owned_tiles = []
		self.trade_routes = []
		self.trade_deals = []

		self.total_science_accrued = 0
		self.culture = 0
		self._gold = 100
		self.faith = 0

		self.current_era = "Ancient"
		self.science_system = ScienceSystem(self)
		self.all_policies = helper.build_policy_objects(dictionary.POLICIES)
		self.unlocked_policies = []
		self.free_policies = [] #how to manage this for oracle and poland?
		self.pantheon = None
		
		self.wonders = []

		self.happiness_points = 400
		self.happiness_points_needed_for_golden_age = 500
		self.in_golden_age = False
		self.golden_age_turns_left = 0 #can this be merged with above?

	@property
	def happiness(self):
		happiness = 9 # Base happiness
		happiness += 4 * len(set(self.luxuries))
		happiness += 1 # +1 for discovering natural wonders
		happiness += sum(city.local_happiness for city in self.cities) # Local city happiness

		if "Meritocracy" in self.unlocked_policies:
			happiness += sum(1 for city in self.cities if city.has_city_connection)

		if "Aristocracy" in self.unlocked_policies:
			happiness += sum(city.population // 10 for city in self.cities)

		capital = next((c for c in self.cities if c.is_capital), None)
		if "Monarchy" in self.unlocked_policies and capital:
			happiness += capital.population // 2

		if self.pantheon == "Goddess of Love":
			happiness += sum(1 for city in self.cities if city.population >= 6)
			
		if self.pantheon == "Sacred Waters":
			pass #hmmmmm need tile refernce in city yeah?
			#happiness += 1 sum(for city in self.cities if city.)

		#need owned tile list?
		#if any(tile.resource == "kailash" for tile in self.owned_tiles):
			#happiness += 2

		# --- Unhappiness calculation ---
		gandhi_city_modifier = 2
		city_unhappiness = 1.8 * len(self.cities) * gandhi_city_modifier

		gandhi_citizen_modifier = 0.5
		meritocracy_modifier = 0.95 if "Meritocracy" in self.unlocked_policies else 1.0

		forbidden_palace_modifier = 1.0
		if "Forbidden Palace" in self.wonders:
			forbidden_palace_modifier = 0.9

		citizen_unhappiness = sum(city.population for city in self.cities) * (gandhi_citizen_modifier * meritocracy_modifier * forbidden_palace_modifier)

		unhappiness = city_unhappiness + citizen_unhappiness

		return math.floor(happiness - unhappiness)

	@property
	def science_per_turn(self):
		total_science = sum(city.science for city in self.cities)

		if self.gold <= 0 and self.gold_per_turn < self.gold: #correct?
			total_science -= abs(self.gold_per_turn)
		if "Rationalism" in self.unlocked_policies:
			total_science *= 1.10

		return max(0, total_science)

	@property
	def culture_per_turn(self):
		culture_per_turn = sum(city.culture for city in self.cities)
		if self.in_golden_age:
			culture_per_turn *= 1.2              
		return culture_per_turn

	@property
	def faith_per_turn(self):
		faith_per_turn = 1 + sum(city.faith for city in self.cities)
		return faith_per_turn

	@property
	def gold(self):
		return self._gold

	@gold.setter
	def gold(self, value):
		self._gold = max(0, value)  # Prevent gold from going below 0

	@property
	def gold_per_turn(self):
		income = sum(city.gold for city in self.cities)

		#wierd next function? this is global gold though im pretty sure, cant do at city level?
		capital = next((c for c in self.cities if c.is_capital), None)
		if "Monarchy" in self.unlocked_policies and capital:
			income += capital.population // 2

		#simulate trading luxes... but we should have a choice to trade for happiness as well?
		#luxury_counts = Counter(self.luxuries)
		#income += sum((count - 1) * 7 for count in luxury_counts.values() if count > 1) #trading simulation... need to offer exchange as well...

		#simulate embassies
		#income += 1 for turns 20, 30, 40, 50, 55, 60, 65, 70
		
		expenses = len(self.improved_tiles) #that are in territory?
		expenses += 2 * len(self.units)
		
		for city in self.cities:
			for building in city.buildings:
				expenses += building.maintenance

		return income - expenses

	def can_found_city(self, unit, engine):
		if not unit:
			result = BoolResult(False, "Unit not found for founding city")
			
		if unit.name != "Settler":
			return BoolResult(False, "Only Settlers can found cities!")

		if unit.moves_left < 1:
			return BoolResult(False, "Not enough movement to found a city!")

		for player in engine.players:
			for city in player.cities:
				if helper.hex_distance(unit.q, unit.r, city.q, city.r) < 4:
					return BoolResult(False, "Too close to another city!")
		return BoolResult(True, "City founding allowed")

	def found_city(self, unit, engine):
		if not (result := self.can_found_city(unit, engine)):
			return result
		
		q, r = unit.q, unit.r
		tile = engine.get_tile(q, r)
		city = City(q, r, engine.current_player)

		from entities import Building

		if len(self.cities) == 0:
			#me no likey
			palace_data = dictionary.BUILDINGS["Palace"]
			palace = Building("Palace", **palace_data)
			palace.completed = True
			city.buildings.append(palace)
			city.is_capital = True

		self.cities.append(city)
		tile.city = city

		tile.owner = self
		for neighbor in helper.tile_neighbors(tile, engine):
			neighbor.owner = self
			
		if tile.luxury:
			self.luxuries.append(tile.resource)
			
		tile.road_complete = True #does this cost?
		#tile.road_progress = 6

		city.update_worked_tiles(engine)
		engine.remove_unit(unit)
		engine.selected_unit = None
		engine.selected_city = city

		#debug
		#engine.spawn_unit(self, "Caravan", q, r)

		return BoolResult(True, "City founded!")

	@property
	def policy_cost(self):
		k = len(self.unlocked_policies) - len(self.free_policies) #free MUST be a subset of unlocked
		n = max(1, len(self.cities))

		cost_per_unlocked_policy = 25 + (6 * k) ** 1.7

		city_penalty = 0.15 * (n - 1)

		if "Representation" in self.unlocked_policies:
			city_penalty *= 0.67

		#is this correct?
		penalty_multiplier = 1 + city_penalty

		base = cost_per_unlocked_policy * penalty_multiplier
		return int(math.ceil(base / 5.0) * 5)
	
	def can_choose_policy(self, policy_name, engine):
		policy = engine.all_policies.get(policy_name)
		
		if not policy:
			return BoolResult(False, "Invalid policy choice.")
	
		if policy.is_unlocked(self):
			return BoolResult(False, "Policy already unlocked.")
	
		if self.culture < self.policy_cost:
			return BoolResult(False, "Not enough culture accrued to unlock this policy.")
	
		#should be called have necessary prereqs
		if not policy.can_unlock(self):
			return BoolResult(False, "You don't meet the prerequisites for this policy.")
		
		if policy.era:
			try:
				era_order = constants.ERAS
				player_era_index = era_order.index(self.current_era)
				required_era_index = era_order.index(policy.era)
			except ValueError:
				return BoolResult(False, f"Internal error: Unknown era '{policy.era}' in policy {policy.name}")
	
			if player_era_index < required_era_index:
				return BoolResult(False, f"{policy.name} requires the {policy.era} Era (you are in {self.current_era}).")
				
		return BoolResult(True, "Policy can be chosen.")

	def choose_policy(self, policy_name, engine):
		if not (result := self.can_choose_policy(policy_name, engine)):
			return result

		policy = engine.all_policies[policy_name]
		self.culture -= self.policy_cost
		self.unlocked_policies.append(policy.name)
		
		if policy.name == "Collective Rule":
			capital = next((c for c in self.cities if c.is_capital), None)
			engine.spawn_unit(self, "Settler", capital.q, capital.r)

		elif policy.name == "Citizenship":
			capital = next((c for c in self.cities if c.is_capital), None)
			engine.spawn_unit(self, "Worker", capital.q, capital.r)

		elif policy.name == "Representation":
			self.start_golden_age()

		elif policy.name == "Legalism":
			for city in self.cities[:4]:
				has_monument = any(b.name == "Monument" for b in city.buildings)
				if not has_monument:
					monument_data = dictionary.BUILDINGS.get("Monument", {})
					free_monument = helper.build_building_object("Monument (FREE)", monument_data)
					free_monument.production_cost = 0
					free_monument.gold_cost = 0
					city.buildings.append(free_monument)

		tradition_policies = ["Tradition", "Aristocracy", "Oligarchy", "Legalism", "Landed Elite", "Monarchy"]
		if all(req in self.unlocked_policies for req in tradition_policies):
			# Add completed Aqueduct building to first four cities.... but should this be RETROactive?
			for city in self.cities[:4]:
				has_aqueduct = any("Aqueduct" in b.name for b in city.buildings)
				if not has_aqueduct:
					aqueduct_data = dictionary.BUILDINGS.get("Aqueduct", {})
					aqueduct = helper.build_building_object("Aqueduct", aqueduct_data)
					#progress = 100
					aqueduct.completed = True
					city.buildings.append(aqueduct)

		liberty_policies = ["Liberty", "Republic", "Citizenship", "Collective Rule", "Representation", "Meritocracy"]
		if all(req in self.unlocked_policies for req in liberty_policies):
			engine.spawn_unit(self, "Great Scientist", capital.q, capital.r) #verify this, also make sure these trigger only ONCE?
			
		return BoolResult(True, f"Unlocked policy: {policy.name}!")

	@property
	def pantheon_threshold(self):
		return 30 #+ 5 * (self.turn // 10)  # Assuming self.turn is updated	

	def can_choose_pantheon(self):
		if self.pantheon:
			return BoolResult(False, "Pantheon already chosen.")
		if self.faith < self.pantheon_threshold:
			return BoolResult(False, "Not enough faith to found a Pantheon.")
		return BoolResult(True, "Pantheon can be chosen.")

	def choose_pantheon(self, pantheon_name):
		if not (result := self.can_choose_pantheon()):
			return result

		self.faith = 0
		self.pantheon = pantheon_name
		return BoolResult(True, f"Pantheon '{pantheon_name}' chosen successfully!")
	
	@property
	def max_trade_routes(self):
		techs = self.science_system.get_unlocked_names()
		trade_techs = {"Compass", "Engineering", "Banking", "Animal Husbandry", "Sailing"}
		#debug
		return sum(1 for tech in trade_techs if tech in self.science_system.get_unlocked_names())

	def start_golden_age(self):
		self.in_golden_age = True
		self.golden_age_turns_left += 10
		self.happiness_points = 0  # reset points on start, what about our policy tho?

	def end_golden_age(self):
		self.in_golden_age = False
		self.golden_age_turns_left = 0

	def update_golden_age(self):
		# Call this every game turn?
		if self.in_golden_age:
			self.golden_age_turns_left -= 1
			if self.golden_age_turns_left <= 0:
				self.end_golden_age()

		if not self.in_golden_age:
			self.happiness_points += max(0, self.happiness)  # Only add if happiness positive

		# Start golden age if threshold reached and not already in one
		if not self.in_golden_age and self.happiness_points >= 500:
			self.start_golden_age()

	def can_end_turn(self):
		if self.culture >= self.policy_cost and len(self.unlocked_policies) < len(self.all_policies):
			return BoolResult(False, "You must select a social policy before ending your turn!")

		if not self.science_system.current_research:
			return BoolResult(False, "You must choose a technology to research before ending your turn!")

		for city in self.cities:
			if city.production_system.current_project is None:
				return BoolResult(False, f"{city.name} needs a production project!")

		if self.faith >= self.pantheon_threshold and not self.pantheon:
			return BoolResult(False, "You must select a pantheon before ending your turn!")

		return BoolResult(True, "Turn may be ended.")

	def end_turn(self, engine):
		if not (result := self.can_end_turn()):
			return result

		unlocked = self.science_system.process_turn_science(self.science_per_turn, self)

		self.gold += self.gold_per_turn
		self.culture += self.culture_per_turn
		self.total_science_accrued += self.science_per_turn
		self.faith += self.faith_per_turn
		
		for unit in self.units:
			if unit.name == "Caravan" and unit.route_active:
				unit.route_turns_remaining -= 1
				if unit.route_turns_remaining <= 0:
					unit.route_active = False
					unit.route_target = None
				else:
					unit.route_target.food += 4 #i dont think this is affected by modifiers?	

		for city in self.cities:
			city.process_growth(engine)

		for u in self.units:
			u.reset_movement()

		self.update_golden_age()

		#culture growth logic?

		engine.end_turn()

		return BoolResult(True, "Turn ended successfully.")
	