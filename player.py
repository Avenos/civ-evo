
import math
import dictionary
import helper
from core import City
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
		self.science = 0
		self.culture = 0
		self._gold = 1000
		self.faith = 0

		self.science_system = ScienceSystem(self)
		self.unlocked_policies = []
		self.pantheon = None

		# New golden age variables:
		self.happiness_points = 470
		self.happiness_points_needed_for_golden_age = 500
		self.in_golden_age = False
		self.golden_age_turns_left = 0

	def can_choose_pantheon(self, current_turn):
		required_faith = 20 + (current_turn // 10) * 5
		return self.pantheon is None and self.faith >= required_faith

	def start_golden_age(self):
		self.in_golden_age = True
		self.golden_age_turns_left = 10
		self.happiness_points = 0  # reset points on start, what about our policy tho?

	def end_golden_age(self):
		self.in_golden_age = False
		self.golden_age_turns_left = 0

	def update_golden_age(self):
		# Call this every game turn
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
	def happiness(self):
		base = 9
		lux_bonus = 4 * len(set(self.improved_tiles))
		nat_wonder_bonus = 1
		local_happiness =  sum(city.local_happiness for city in self.cities)
		city_penalty = -3.6 * len(self.cities)
		pop_penalty = -0.5 * sum(city.population for city in self.cities)

		total_happiness = base + lux_bonus + nat_wonder_bonus + city_penalty + pop_penalty
		return math.floor(total_happiness)

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
		income = 20 + sum(city.gold for city in self.cities)

		# Count duplicates in luxuries
		luxury_counts = Counter(self.luxuries)
		duplicates_bonus = sum((count - 1) * 7 for count in luxury_counts.values() if count > 1)

		tile_maintenance_cost = len(self.improved_tiles)
		unit_maintenance_cost = 2 * len(self.units)
		# building_maintenance_cost = sum(city.building_maintenance_cost for city in self.cities)

		total_maintenance = tile_maintenance_cost + unit_maintenance_cost

		return income + duplicates_bonus - total_maintenance

	@property
	def policy_cost(self):
		k = len(self.unlocked_policies)
		n = max(1, len(self.cities))

		cost_per_unlocked_policy = 25 + (6 * k) ** 1.7

		base_penalty = 0.15 * (n - 1)

		if "Representation" in self.unlocked_policies:
			base_penalty *= 0.67  # reduce penalty by 33%

		penalty_multiplier = 1 + base_penalty

		base = cost_per_unlocked_policy * penalty_multiplier
		return int(math.ceil(base / 5.0) * 5)


	def choose_policy(self, policy_name, game):
		policy = game.all_policies.get(policy_name)
		if not policy:
			game.show_message("Invalid policy choice!", 120)
			return False

		if policy.is_unlocked(self):
			game.show_message("Policy already unlocked!", 120)
			return False

		if not policy.can_unlock(self):
			game.show_message("You don't meet the prerequisites for this policy!", 120)
			return False

		if self.culture < self.policy_cost:
			game.show_message("Not enough culture to unlock this policy!", 120)
			return False

		self.culture -= self.policy_cost
		self.unlocked_policies.append(policy.name)
		game.show_message(f"Unlocked policy: {policy.name}!", 120)

		if policy.name == "Collective Rule":
			spawn_unit_near_capital(self, game, "Settler", "A free Settler has arrived!")

		if policy.name == "Citizenship":
			spawn_unit_near_capital(self, game, "Worker", "A free Worker has arrived!")

		if policy.name == "Legalism":
			# Monument (FREE) in first four cities if they don't already have a Monument
			for city in self.cities[:4]:
				has_monument = any("Monument" in b.name for b in city.buildings)
				if not has_monument:
					monument_data = dictionary.BUILDINGS.get("Monument", {})
					free_monument = Building(
		            name="Monument (FREE)",
		                            food=monument_data.get("food", 0),
		                                production=monument_data.get("production", 0),
		                                gold=monument_data.get("gold", 0),
		                                science=monument_data.get("science", 0),
		                                culture=monument_data.get("culture", 0),
		                                happiness=monument_data.get("happiness", 0),
		                                growth_percentage=monument_data.get("growth_percentage", 0),
		                                science_percentage=monument_data.get("science_percentage", 0),
		                                production_cost=0,
		                                gold_cost=0
		    )
					city.buildings.append(free_monument)
					game.show_message(f"{city.name} receives a free Monument!", 90)

		return True

	def end_turn(self, game):
		# Check for policy selection requirement
		if self.culture >= self.policy_cost and len(self.unlocked_policies) < len(game.all_policies):
			game.show_message("You must select a social policy before ending your turn!", 180)
			return False

		# Check tech research selection first (no progress yet)
		if not self.science_system.current_research:
			game.show_message("You must choose a technology to research before ending your turn!", 180)
			return False

		# Check production projects in cities
		for city in self.cities:
			if not city.production_system.current_project:
				game.show_message(f"{city.name} needs a production project!", 90)
				return False

		# Check Pantheon selection if faith threshold met
		if self.pantheon is None:
			required_faith = 20 + (game.turn // 10) * 5
			if self.faith >= required_faith:
				game.show_message("You must select a Pantheon before ending your turn!", 180)
				return False

		# All checks passed, now apply turn-end effects:

		# Apply science progress and notify if tech unlocked
		unlocked = self.science_system.process_turn_science(self.science_per_turn, self)

		if unlocked:
			game.show_message(f"Tech Unlocked: {unlocked}!", 120)

		# Apply resource yields
		self.gold += self.gold_per_turn
		self.culture += self.culture_per_turn
		self.science += self.science_per_turn
		self.faith += self.faith_per_turn

		# Process city growth and tile updates
		for city in self.cities:
			city.process_growth()
			city.update_worked_tiles(game)

		# Reset units' turns
		for u in self.units:
			u.reset_turn()

		# Update golden age state
		self.update_golden_age()

		return True


	def found_city(self, unit, game):
		q, r = unit.q, unit.r

		if unit.name != "Settler":
			game.show_message("Only Settlers can found cities!", 90)
			return

		if unit.moves_left < 1:
			game.show_message("Not enough movement to found a city!", 90)
			return

		for player in game.players:
			for city in player.cities:
				if helper.hex_distance(q, r, city.q, city.r) < 4:
					game.show_message("Too close to another city!", 90)
					return

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
		game.territory.add((q, r))

		for nq, nr in helper.hex_neighbors(q, r):
			if 0 <= nq < GRID_WIDTH and 0 <= nr < GRID_HEIGHT:
				game.territory.add((nq, nr))
				game.tiles[nq][nr].territory = True

		game.tiles[q][r].territory = True
		city.update_worked_tiles(game)
		self.remove_unit(unit, game)
		game.selected_city = city


	def remove_unit(self, unit, game):
		q, r = unit.q, unit.r
		game.tiles[q][r].unit = None
		self.units.remove(unit)
