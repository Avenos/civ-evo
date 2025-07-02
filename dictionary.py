
#deadless switch
#list of legal actions for EA
#tile improvement system, add dict improvement values, also adjacency bonuses for different tile types? flood plains? marsh?
#citizen tile assignment choice system, #if city grows auto update the next worked tile to highest production tile then by gold 
#purchase system finalize, purhcased things landing on same tile... stacking system? terrible unit spawning code
#verify forests at top part of minimap #define all rivers, add columns
#make ui nice food decimal rounding? or floor?
#border growth algorithm and formula 15 25 40 north cotton then dyes them cotton
#speed monitoring and efficiency
#terrain stuff lower case? why be consistent....
#tile purchasing cost
#does pop growth help expand borders? ancient ruins?
#do we let the AI CHOOSE between pop and culture and free tech? yeah. whatever it wants.
#action API finalize!
#verify science system overflow, display?
#DE-select production projects each turn if they are no longer valid after all relevant actions. production applied at BEGINNING of turn. 1 turn left on NC and buiilt a city? it doesnt complete. right?
#policies effects! finalize
#pantheon system finalize impllement do NEW cities not auto get pantheons or do they?
#verify starvation and aqueducts
#city connections verify
#program all building effects, stoneworks, stable, lighthouse, verify aqeuduct, etc
#city itself tile yield values? settling on luxes also city roads maintenance?? 
#negative gold penalties check
#trade routes caravans ability
#roads? machinery? bridges over rivers?
#figure out gpt formula: 1war and 1 worker =  1gpt
#player era and policy tree prereqs
#golden age verify tile gold also point req func, stacking?
#happiness, gold and culture are ints?

#embassies sim
#yield icons and toggle
#meeting people tech boost? machinery road movement
#wonders allowed toa by 42 pyramids by 52 else gold?
#great person slots

#RL or EA TO TURN 121!!!
##hover formulas? map importer? standard map size? reserarch agreements? sell buildings? FREE policies pretend we are poland?

PLAYER_COLORS = [
	(0, 255, 0, 50),       # Player 0 — Green
	(0, 0, 255, 50),       # Player 1 — Blue
	(255, 0, 0, 50),       # Player 2 — Red
	(255, 255, 0, 50),     # Player 3 — Yellow
	(255, 165, 0, 50),     # Player 4 — Orange
	(128, 0, 128, 50),     # Player 5 — Purple
    (0, 255, 255, 50),     # Player 6 — Cyan
    (255, 192, 203, 50),   # Player 7 — Pink
]

# Edge indices: clockwise from E = 0
DIRECTION_TO_EDGE = {
	"E": 0,
	"NE": 5,
	"NW": 4,
	"W": 3,
	"SW": 2,
	"SE": 1,
}

# Neighbor offsets for odd-r horizontal layout
EVEN_ROW_NEIGHBORS = {
	"E": (1, 0),
	"NE": (0, -1),
	"NW": (-1, -1),
	"W": (-1, 0),
	"SW": (-1, 1),
	"SE": (0, 1),
}

ODD_ROW_NEIGHBORS = {
	"E": (1, 0),
	"NE": (1, -1),
	"NW": (0, -1),
	"W": (-1, 0),
	"SW": (0, 1),
	"SE": (1, 1),
}

OPPOSITE_DIRECTION = {
	"E": "W",
	"NE": "SW",
	"NW": "SE",
	"W": "E",
	"SW": "NE",
	"SE": "NW",
}

UNITS = {
	"Settler": {"moves": 2, "hp": 100, "production_cost": 106, "gold_cost": 500},
	"Worker": {"moves": 2, "production_cost": 70, "hp": 100, "gold_cost": 220},
	"Scout": {"moves": 2, "production_cost": 25, "hp": 100, "gold_cost": 140},
	"Warrior": {"moves": 2,  "production_cost": 40,"hp": 100, "gold_cost": 200},
	"Caravan": {"moves": 0, "hp": 100, "techs_required": ["Animal Husbandry"], "production_cost": 75, "gold_cost": 390},
	"Great Scientist": {"moves": 2, "hp": 100},
	"Great Engineer": {"moves": 2, "hp": 100},
}

BUILDINGS = {
	"Palace": {"science": 3, "production": 3, "gold": 3, "culture": 1}, #Implemented
	"Library": {"maintenance": 1, "production_cost": 75, "techs_required": ["Writing"], "gold_cost": 400}, #Implemented
	"Shrine": {"maintenance": 1, "faith": 1, "production_cost": 40, "techs_required": ["Pottery"], "gold_cost": 250}, #Implemented
	"Monument": {"maintenance": 1,  "culture": 2, "production_cost": 40, "gold_cost": 280}, #Implemented
	"Monument (Free)": {"culture": 2}, #Implemented
	"Granary": {"maintenance": 1, "food": 2, "growth_percentage": 0.1, "production_cost": 60, "techs_required": ["Pottery"], "gold_cost": 340}, #Implemented
	"Water Mill": {"maintenance": 2, "food": 2, "production": 1, "production_cost": 75, "techs_required": ["The Wheel"], "gold_cost": 400}, #Implemented
	"Temple of Artemis": {"culture": 1, "production_cost": 185, "techs_required": ["Archery"], "wonder": True}, #Implemented except GE point and ranged bonus
	"Stone Works": {"maintenance": 1, "production_cost": 75, "techs_required": ["Calendar"], "gold_cost": 320}, #city must have a quarry
	"Forge": {},
	"Lighthouse": {},
	"Stable": {"maintenance": 1, "production_cost": 100, "techs_required": ["Horseback Riding"], "gold_cost": 500},
	"Pyramids": {"production_cost": 185, "techs_required": ["Masonry"], "policies_required": ["Liberty"], "wonder": True},
	"National College": {"science": 3, "science_percentage": 0.5, "production_cost": 125, "techs_required": ["Philosophy"], "national_wonder": True}, #production_cost depends on cities...
	"Oracle": {"culture": 3, "production_cost": 250, "techs_required": ["Philosophy"], "wonder": True}, #gs point
	"Hanging Gardens": {"food": 6, "culture": 1, "production_cost": 250, "techs_required": ["Mathematics"], "policies_required": ["Tradition"], "wonder": True}, #Implemented
	"Circus": {"happiness": 2, "production_cost": 75, "techs_required": ["Trapping"], "gold_cost": 400}, #must have upgraded horses or ivory
	"Circus Maximus": {"happiness": 5, "culture": 1, "production_cost": 125, "techs_required": ["Horseback Riding"], "national_wonder": True}, #Implemented
	"Lighthouse": {"maintenance": 1, "production_cost": 75, "techs_required": ["Optics"], "gold_cost": 400},
	"Aqueduct": {"maintenance": 1, "production_cost": 100, "techs_required": ["Engineering"], "gold_cost": 400}, #Implemented should probably test
	"Colosseum": {"maintenance": 1, "happiness": 2, "production_cost": 100, "techs_required": ["Construction"], "gold_cost": 500}, #Implemented
	"University": {"maintenance": 2, "science_percentage": 0.33, "production_cost": 160, "techs_required": ["Education"], "buildings_required": ["Library"], "gold_cost": 660}, #GS slots
	"Market": {"gold": 1, "production_cost": 100, "techs_required": ["Currency"], "gold_cost": 500},
	"Mint": {"production_cost": 100, "techs_required": ["Currency"], "gold_cost": 500}, #Implemented
	"Artists' Guild": {"maintenance": 1, "production_cost": 150, "techs_required": ["Guilds"], "national_wonder": True},
	"Writers' Guild": {"maintenance": 1, "production_cost": 100, "techs_required": ["Drama and Poetry"], "national_wonder": True},
	"Workshop": {"production": 2, "production_percentage": 0.1, "maintenance": 2, "production_cost": 120, "techs_required": ["Metal Casting"], "gold_cost": 580}, #allow production trade routes, GE point
	"Ironworks": {"production": 8, "culture": 1, "production_cost": 125, "techs_required": ["Machinery"], "national_wonder": True}, #production_cost depends on cities...
	"Observatory": {"science_percentage": 0.5, "production_cost": 200, "techs_required": ["Astronomy"], "gold_cost": 780}, #Implemented
	"Garden": {"maintenance": 1, "production_cost": 120, "techs_required": ["Theology"], "gold_cost": 580}, #City must border a source of fresh water
	"Forbidden Palace": {"culture": 1, "production_cost": 500, "techs_required": ["Banking"], "policies_required": ["Patronage"], "wonder": True}, #Implemented
	"Notre Dame": {"happiness": 10, "faith": 4, "culture": 1, "production_cost": 400, "techs_required": ["Physics"], "wonder": True} #Implemented except GM point, 1 culture?
}

RESOURCES = {
	"wheat":    {"food": 1},
	"iron":     {"production": 1},
	"horses":   {"production": 1},
	"deer":     {"food": 1},
	"sheep":   {"food": 1},
	"cattle":   {"food": 1},
	"oasis":   {"food": 3, "gold": 1},
	"salt":   {"food": 1, "gold": 1},
	"citrus":   {"food": 1, "gold": 1},
	"incense":   {"gold": 2},
	"spices":   {"gold": 2},
	"silk":   {"gold": 2},
	"silver":   {"gold": 2},
	"gems":   {"gold": 3},
	"cotton":   {"gold": 2},
	"dyes":   {"gold": 2},
	"truffles":   {"gold": 2},
	"ivory":   {"gold": 2},
	"stone":   {"production": 1},
	"sugar":   {"gold": 2},
	"bananas":   {"food": 1},
	"gold":     {"gold": 2},
	"marble":   {"gold": 2},
	"kailash":   {"faith": 6}, #also happiness
	"fish":     {"food": 1},
	"whales":   {"food": 1, "gold": 1},
	"crab":     {"gold": 2},
	"pearls":     {"gold": 2},
	"n":     {},
}

IMPROVEMENTS = {
	"farm": {"requires": "wheat"},
	"mine": {"requires": "hill"},
	"pasture": {"requires": ["cattle", "sheep", "horses"]}, #Implemented
	"plantation": {"requires": ["citrus", "incense", "spices", "dyes", "cotton", "sugar", "bananas"]},
	"quarry": {"requires": ["stone", "marble"]},
	"camp": {"requires": ["ivory", "truffles", "deer"]}, #forest allowed, chopping removes camp.
	"trading post": {}, #forst and jungle allowed?
	"road": {},
	"none": {},
}

TECHS = {
	"Agriculture": {"base_cost": 20, "prerequisites": []},
	"Pottery": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #allows granary and shrine
	"Animal Husbandry": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #reveals horses on map, allows caravans, pastures, +1 trade route
	"Archery": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #allows toa and archer
	"Mining": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #mines and chopping forests

	"Sailing": {"base_cost": 55, "prerequisites": ["Pottery"]}, #extra trade route
	"Calendar": {"base_cost": 55, "prerequisites": ["Pottery"]}, #stone works and plantations
	"Writing": {"base_cost": 55, "prerequisites": ["Pottery"]}, #library
	"Trapping": {"base_cost": 55, "prerequisites": ["Animal Husbandry"]}, #camps and circus
	"The Wheel": {"base_cost": 55, "prerequisites": ["Animal Husbandry", "Archery"]}, #water mill and roads
	"Masonry": {"base_cost": 55, "prerequisites": ["Mining"]}, #pyramids, quarry, clear marsh
	"Bronze Working": {"base_cost": 55, "prerequisites": ["Mining"]}, #reveal iron, remove jungle

	"Optics": {"base_cost": 85, "prerequisites": ["Sailing"]}, #lighthouse
	"Horseback Riding": {"base_cost": 105, "prerequisites": ["Trapping", "The Wheel"]}, #stable, circus maximus
	"Mathematics": {"base_cost": 105, "prerequisites": ["The Wheel"]}, #hanging gardens
	"Construction": {"base_cost": 105, "prerequisites": ["The Wheel", "Masonry"]}, #colosseum, lumber mill

	"Philosophy": {"base_cost": 175, "prerequisites": ["Calendar", "Writing"]}, #nat college, oracle
	"Drama and Poetry": {"base_cost": 175, "prerequisites": ["Writing"]}, #writers guild"
	"Currency": {"base_cost": 175, "prerequisites": ["Mathematics"]}, #mint, market
	"Engineering": {"base_cost": 175, "prerequisites": ["Mathematics", "Construction"]}, #aqueduct, bridge over river, extra trade route
	"Iron Working": {"base_cost": 175, "prerequisites": ["Bronze Working"]}, #check cost

	"Theology": {"base_cost": 275, "prerequisites": ["Philosophy", "Drama and Poetry"]},
	"Civil Service": {"base_cost": 275, "prerequisites": ["Drama and Poetry", "Horseback Riding", "Currency"]}, #fresh water farms +1
	"Guilds": {"base_cost": 275, "prerequisites": ["Currency"]}, #trading posts
	"Metal Casting": {"base_cost": 275, "prerequisites": ["Engineering", "Iron Working"]}, #forge and workshop

	"Compass": {"base_cost": 375, "prerequisites": ["Optics"]}, #Extra trade route, check cost?
	"Education": {"base_cost": 485, "prerequisites": ["Theology", "Civil Service"]}, #university, allow research agreements
	"Chivalry": {"base_cost": 485, "prerequisites": ["Civil Service", "Guilds"]}, #mughal fort eh...
	"Machinery": {"base_cost": 485, "prerequisites": ["Guilds", "Engineering"]}, #ironworks, faster road movement
	"Physics": {"base_cost": 485, "prerequisites": ["Metal Casting"]}, #Notre Dame
	"Steel": {"base_cost": 485, "prerequisites": ["Metal Casting"]},

	"Astronomy": {"base_cost": 780, "prerequisites": ["Compass", "Education"]}, #observatory
	"Acoustics": {"base_cost": 780, "prerequisites": ["Education"]}, #sistine chapel*
	"Banking": {"base_cost": 780, "prerequisites": ["Education", "Chivalry"]}, #bank, forbidden palace, trade route
	"Printing Press": {"base_cost": 780, "prerequisites": ["Chivalry", "Machinery", "Physics"]}, #zoo, leaning tower*
	"Gunpowder": {"base_cost": 780, "prerequisites": ["Physics", "Steel"]}
}

POLICIES = {
	"Tradition": {"desc": "Greatly increases rate of border growth. +3 Culture. Allows hanging gardens", "prerequisites": []}, #Implemented except border
	"Aristocracy": {"desc": "+1 happiness for every 10 citizens in a city. +15% wonder production", "prerequisites": ["Tradition"]}, #Implemented happ
	"Oligarchy": {"desc": "Units in cities cost no maintenance", "prerequisites": ["Tradition"]},
	"Legalism": {"desc": "First four cities get a FREE monument if they don't already have one", "prerequisites": ["Oligarchy"]}, #Implemented
	"Landed Elite": {"desc": "+2 food and +10% excess food in the capitol", "prerequisites": ["Legalism"]}, #Implemented
	"Monarchy": {"desc": "+1 gold and -1 unhappiness for every 2 citizens in the capital", "prerequisites": ["Legalism"]}, #Implemented
	#free aqueduct and 15% growth in first four cities upon completion #Implemented aqeuduct retroactive?

	"Liberty": {"desc": "+1 culture per city. Allows pyramids", "prerequisites": []}, #Implemented
	"Republic": {"desc": "+1 production per city, 5% more building production", "prerequisites": ["Liberty"]}, #Implemented
	"Citizenship": {"desc": "Immediate worker, workers upgrade tiles 25% faster", "prerequisites": ["Liberty"]},
	"Collective Rule": {"desc": "Immediate settler, settlers cost 50% less.", "prerequisites": ["Republic"]},
	"Representation": {"desc": "Immediate golden age, culture cost from extra cities is 33% less", "prerequisites": ["Citizenship"]}, #Implemented
	"Meritocracy": {"desc": "+1 happiness for each city connected to capitol, also -5% unhappiness from citizens", "prerequisites": ["Citizenship"]}, #Implemented
	#great scientist/engineer upon completion

	"Patronage": {"desc": "City state rep is more resilient. Allows forbidden palace", "prerequisites": ["classical era?"]}, #Implemented
	"Commerce": {"desc": "Gold yields up 25% in capital. Allows big ben", "prerequisites": ["medieval era?"]}, #Implemented

	"Rationalism": {"desc": "Global science up 10%. Allows porcelain tower", "prerequisites": ["rennaisance era"]} #Implemented
}

PANTHEONS = {
	"Oral Tradition": {"desc": " +1 Culture from Plantations"}, #Implemented
	"Goddess of Love": {"desc": " +1 Happiness from cities with Population of 6+"}, #Implemented
	"God of Craftsmen": {"desc": "+1 Production in cities with Population of 3+"}, #Implemented
	"Fertility Rites": {"desc": "+10% Growth in all cities"}, #Implemented
	"Goddess of the Hunt": {"desc": "+1 Food from Camps"}, #Implemented
	"God-King": {"desc": "+1 of each: Faith, Culture, Gold, Science, Production in Capital"}, #Implemented
	"Messenger of the Gods": {"desc": "2 Science in cities with a City Connection"}, #Implemented
	"Sacred Waters": {"desc": "+1 Happiness from cities on rivers"},
	"Sun God": {"desc": "+1 Food for each Bananas, Citrus, and Wheat resource"}, #Implemented
	"One with Nature": {"desc": "+4 faith from natural wonders"}, #Implemented for kailash only
}

# Influence cost lookup by terrain/feature
INFLUENCE_COST = {
	"Atoll": -1, "Coast": 2, "Desert": 2, "Floodplains": -1, "Forest": 1,
	"Grassland": 1, "Hill": 1, "Ice": 3, "Jungle": 1, "Lake": 2, "Mountain": 3,
	"Natural Wonder": 3, "Oasis": -1, "Ocean": 3, "Plains": 1, "Snow": 2,
	"Swamp": 1, "Tundra": 2
}

# Priority multipliers
MULTIPLIERS = {
	"DISTANCE": 100,
	"RESOURCE": -105,
	"WATER": 25,
	"UNWORKABLE": 100,
	"IMPROVEMENT": -5,
	"BARB_CAMP": 100,
	"ROAD": 0,
	"NATURAL_WONDER": -105,
	"YIELD_POINT": -1,
	"NO_ADJACENT_OWNED": 1000
}

TERRAIN_TYPES =  {
	"p": {"name": "plains", "food": 1, "production": 1},
	"g": {"name": "grassland", "food": 2},
	"d": {"name": "desert"},
	"t": {"name": "tundra", "food": 1},
	"s": {"name": "snow"},
	"c": {"name": "coast", "food": 1},
	"o": {"name": "ocean", "food": 1},
	"n": {"name": "none"},
	"l": {"name": "lake", "food": 2},
}