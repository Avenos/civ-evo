
import math
import dictionary
import helper
from city import City
from systems import ScienceSystem
from collections import Counter
from constants import GRID_WIDTH, GRID_HEIGHT

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
		self._gold = 1000
		self.faith = 0

		self.science_system = ScienceSystem(self)
		self.all_policies = helper.build_policy_objects(dictionary.POLICIES)
		self.unlocked_policies = []
		self.free_policies = [] #how to manage this for oracle and poland?
		self.pantheon = None

		self.happiness_points = 400
		self.happiness_points_needed_for_golden_age = 500
		self.in_golden_age = False
		self.golden_age_turns_left = 0 #can this be merged with above?

	@property
	def max_trade_routes(self):
		techs = self.science_system.get_unlocked_names()
		trade_techs = {"Compass", "Engineering", "Banking", "Animal Husbandry", "Sailing"}
		return sum(1 for tech in trade_techs if tech in techs)

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

	@property
	def max_trade_routes(self):
		trade_route_techs = {
			"Sailing",
			"Animal Husbandry",
			"Engineering",
			"Compass",
			"Banking"
		}
		return sum(1 for tech in trade_route_techs if tech in self.science_system.unlocked_techs)

	@property
	def happiness(self):
		happiness = 9 # Base happiness
		happiness += 4 * len(set(self.improved_tiles)) # +4 happiness for each unique luxury resource
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

		#need owned tile list?
		#if any(tile.resource == "kailash" for tile in self.owned_tiles):
			#happiness += 2

		# --- Unhappiness calculation ---
		gandhi_city_modifier = 2
		city_unhappiness = 1.8 * len(self.cities) * gandhi_city_modifier

		gandhi_citizen_modifier = 0.5
		meritocracy_modifier = 0.95 if "Meritocracy" in self.unlocked_policies else 1.0

		#expensive?
		forbidden_palace_modifier = 1.0 #defining as 1 here feels wierd
		for city in self.cities:
			if any(b.name == "Forbidden Palace" and b.completed for b in city.buildings):
				forbidden_palace_modifier = 0.9
				break

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

		#wierd next function?
		capital = next((c for c in self.cities if c.is_capital), None)
		if "Monarchy" in self.unlocked_policies and capital:
			income += capital.population // 2

		luxury_counts = Counter(self.luxuries)
		income += sum((count - 1) * 7 for count in luxury_counts.values() if count > 1) #trading simulation... need to offer exchange as well...

		expenses = len(self.improved_tiles) #that are in territory?
		expenses += 2 * len(self.units)
		#building maintenance cost is the sum of all maintenance on all buildings in all cities? i dont think its local...

		return income - expenses

	@property
	def policy_cost(self):
		k = len(self.unlocked_policies) - len(self.free_policies) #free MUST be a subset of unlocked
		n = max(1, len(self.cities))

		cost_per_unlocked_policy = 25 + (6 * k) ** 1.7

		city_penalty = 0.15 * (n - 1)

		if "Representation" in self.unlocked_policies:
			city_penalty *= 0.67

		penalty_multiplier = 1 + city_penalty

		base = cost_per_unlocked_policy * penalty_multiplier
		return int(math.ceil(base / 5.0) * 5)

	def can_choose_policy(self, policy_name, game):
		policy = game.all_policies.get(policy_name)
		if not policy:
			return False, "Invalid policy choice."

		if policy.is_unlocked(self):
			return False, "Policy already unlocked."
		
		if self.culture < self.policy_cost:
			return False, "Not enough culture accrued to unlock this policy."	

		#no like
		if not policy.can_unlock(self):
			return False, "You don't meet the prerequisites for this policy."


		return True, "Policy can be chosen."

	def choose_policy(self, policy_name, game):
		success, message = self.can_choose_policy(policy_name, game)
		if not success:
			return False, message

		policy = game.all_policies[policy_name]
		self.culture -= self.policy_cost
		self.unlocked_policies.append(policy.name)

		# Apply immediate policy bonuses
		if policy.name == "Collective Rule":
			helper.spawn_unit_near_capital(self, game, "Settler", "A free Settler has arrived!")

		elif policy.name == "Citizenship":
			helper.spawn_unit_near_capital(self, game, "Worker", "A free Worker has arrived!")

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

		required_policies = ["Tradition", "Aristocracy", "Oligarchy", "Legalism", "Landed Elite", "Monarchy"]
		if all(req in self.unlocked_policies for req in required_policies):
			# Add completed Aqueduct building to first four cities.... but should this be RETROactive?
			for city in self.cities[:4]:
				has_aqueduct = any("Aqueduct" in b.name for b in city.buildings)
				if not has_aqueduct:
					aqueduct_data = dictionary.BUILDINGS.get("Aqueduct", {})
					aqueduct = helper.build_building_object("Aqueduct", aqueduct_data)
					#progress = 100
					aqueduct.completed = True
					city.buildings.append(aqueduct)

		return True, f"Unlocked policy: {policy.name}!"

	@property
	def pantheon_threshold(self):
		return 100 #+ 5 * (self.turn // 10)  # Assuming self.turn is updated	

	def can_choose_pantheon(self):
		if self.pantheon:
			return False, "Pantheon already chosen."
		if self.faith < self.pantheon_threshold:
			return False, "Not enough faith to found a Pantheon."
		return True, "Pantheon can be chosen."

	def choose_pantheon(self, pantheon_name):
		success, msg = self.can_choose_pantheon()

		if not success:
			return False, message

		self.faith = 0
		self.pantheon = pantheon_name
		return True, f"Pantheon '{pantheon_name}' chosen successfully!"

	def can_end_turn(self):
		if self.culture >= self.policy_cost and len(self.unlocked_policies) < len(self.all_policies):
			return False, "You must select a social policy before ending your turn!"

		if not self.science_system.current_research:
			return False, "You must choose a technology to research before ending your turn!"

		for city in self.cities:
			if not city.production_system.current_project:
				return False, f"{city.name} needs a production project!"
		
		if self.faith >= self.pantheon_threshold and not self.pantheon:
			return False, "You must select a Pantheon before ending your turn!"
		
		return True, "Turn may be ended."

	def end_turn(self, game):
		success, message = self.can_end_turn()
		
		if not success:
			return success, message
		
		unlocked = self.science_system.process_turn_science(self.science_per_turn, self)

		self.gold += self.gold_per_turn
		self.culture += self.culture_per_turn
		self.total_science_accrued += self.science_per_turn
		self.faith += self.faith_per_turn

		# Process city growth and tile updates
		for city in self.cities:
			city.process_growth()
			city.update_worked_tiles(game) #?

		# Reset units' turns
		for u in self.units:
			u.reset_movement()

		# Update golden age state
		self.update_golden_age()

		#culture growth logic?
		
		game.end_turn()

		return True, "Turn ended successfully."

	def can_found_city(self, unit, game):
		q, r = unit.q, unit.r

		if unit.name != "Settler":
			return False, "Only Settlers can found cities!"

		if unit.moves_left < 1:
			return False, "Not enough movement to found a city!"

		for player in game.players:
			for city in player.cities:
				if helper.hex_distance(q, r, city.q, city.r) < 4:
					return False, "Too close to another city!"
		return True, "City founding allowed."

	def found_city(self, unit, game):
		q, r = unit.q, unit.r

		allowed, message = self.can_found_city(unit, game)
		if not allowed:
			return False, message
		else:
			city = City(q, r, game.current_player)

			from core import Building

			if len(self.cities) == 0:
				palace_data = dictionary.BUILDINGS["Palace"]
				palace = Building("Palace", **palace_data)
				palace.completed = True  # ← This is crucial
				city.buildings.append(palace)
				city.is_capital = 1

			self.cities.append(city)
			game.tiles[q][r].city = city

			game.tiles[q][r].owner = self
			for nq, nr in helper.hex_neighbors(q, r):
				game.tiles[nq][nr].owner = self

			city.update_worked_tiles(game)
			game.remove_unit(unit)
			game.selected_unit = None
			game.selected_city = city

			return True, None