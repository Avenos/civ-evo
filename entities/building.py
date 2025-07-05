
class Building:
	def __init__(self, name, food=0, production=0, gold=0, maintenance=0, science=0, culture=0, faith =0, happiness=0, growth_percentage=0, production_percentage=0, science_percentage=0, gold_percentage = 0, production_cost=0, gold_cost=0, techs_required=None, policies_required=None, buildings_required=None, wonder=False, national_wonder=False):
		self.name = name
		self.type = "building"
		self.food = food
		self.production = production
		self.gold = gold
		self.maintenance = maintenance
		self.science = science
		self.culture = culture
		self.faith = faith
		self.happiness = happiness
		self.growth_percentage = growth_percentage
		self.production_percentage = production_percentage
		self.science_percentage = science_percentage
		self.gold_percentage = gold_percentage

		self.production_cost = production_cost
		self.producable = production_cost > 0
		self.gold_cost = gold_cost
		self.purchasable = gold_cost > 0

		self.techs_required = techs_required or []
		self.policies_required = policies_required or []
		self.buildings_required = buildings_required or []

		self.wonder = wonder
		self.national_wonder = national_wonder
		self.progress = 0 #pass in for free stuff?
		self.completed = False #pass in for free stuff? merge with above 100?
