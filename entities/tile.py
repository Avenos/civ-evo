
#here is tile.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

from data import dictionary

class Tile:
	def __init__(self, q, r, terrain_type, elevation, trees, resource):
		self.q = q
		self.r = r
		self.terrain_type = terrain_type
		self.elevation = elevation
		self.trees = trees
		self.resource = resource
		self.luxury = dictionary.RESOURCES.get(self.resource, {}).get("luxury", False)
		self.city = None
		self.owner = None

		self.improvement = None
		self.improvement_progress = 0
		self.improvement_complete = False
		self.road_progress = 0
		self.road_complete = False

		self.unit = None  # or maybe a list if you support stacking in the future
		self.rivers = set()  # Set of edge indices (0 through 5) with rivers
		self.fresh_water = False
		self.ancient_ruin = None
		self.worked_by = None # needs to be set in update tiles?

		#why is this here?
		self.terrain_data = dictionary.TERRAIN_TYPES[terrain_type]

		if self.elevation == 2 or self.terrain_type in ("o", "c", "l"):
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
		if self.city: #is this correct? what about settle on 3 food tile?
			base_food = 2
		elif self.terrain_type == "snow":
			base_food = 0
		elif self.trees == 2: # Jungle
			base_food = 2
		elif self.trees == 1: # Forest
			base_food = 1
		elif self.elevation == 1: # Hill with no trees
			base_food = 0
		else:
			base_food = self.terrain_data.get("food", 0)

		resource_food = dictionary.RESOURCES.get(self.resource, {}).get("food", 0)

		if self.worked_by: #this is actually needed otherwise granary bonus applies to all cities
			if any("Granary" in b.name for b in self.worked_by.buildings):
				if self.resource in ["wheat", "deer", "bananas"]: #what type of brackets here?
					resource_food += 1
			if any("Lighthouse" in b.name for b in self.worked_by.buildings):
				if self.resource == "fish":
					resource_food += 1
				if self.terrain_type in ["c", "o"]:
					resource_food += 1

		if self.owner:
			if self.owner.pantheon == "Sun God":
				if self.resource in ["wheat", "citrus", "bananas"]:
					resource_food += 1

			if self.improvement == "Camp" and self.owner.pantheon == "Goddess of the Hunt":
				resource_food += 1

		#fix?
		if self.improvement == "Pasture" and self.improvement_complete and self.resource == "sheep":
			resource_food += 1

		#need more logic here
		if self.improvement == "Farm" and self.improvement_complete:
			resource_food += 1 #2 if civil service and fresh water

		return base_food + resource_food #++

	@property
	def production(self):
		player = self.owner
		
		if self.city: #is this correct? snow even hill is one prod...
			base_production = 1 + self.elevation
		elif self.terrain_type == "s":
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

		if self.improvement == "Pasture" and self.improvement_complete and (self.resource == "horses" or self.resource == "cattle" ):
			resource_production += 1

		if self.improvement == "Mine" and self.improvement_complete:
			resource_production += 1

		if self.worked_by: #this is actually needed otherwise lighthouse bonus applies to all cities
			if any("Lighthouse" in b.name for b in self.worked_by.buildings):
				if self.resource in ["fish", "pearls", "whales", "crab"]: #what type of brackets here?
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

		if self.improvement == "Trading Post" and self.improvement_complete:
			gold += 1

		return gold

	@property
	def science(self):
		science = self.terrain_data.get("science", 0)

		if self.improvement == "Academy" and self.improvement_complete:
			science += 8

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
		faith = 0

		if self.owner and self.owner.pantheon == "Desert Folklore" and self.terrain_type == 'd':
			faith +=1

		if self.resource == "kailash":
			if self.owner and self.owner.pantheon == "One with Nature":
				faith += 10
			else:
				faith += 6
		return faith
