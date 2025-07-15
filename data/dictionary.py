
#turn 121 to beat:
#science +195, 6 turns till banking
#crop yield 200, 10 cities total
#86 hammers
#27 culture per turn
#900 + 97 gold per turn

#major:
#building project instances and completion
#worked tile bullshit, lock in settler prod tiles?
#clear up actionhandler checks?
#finalize tile improvement system, and all dependent bonuses, flood plains? marsh?
#forced actions? end turn just doesnt show up... but how does it know which are required
#border growth algorithm and formula 15 25 40 north cotton then dyes them cotton
#roads? machinery? bridges over rivers? chopping also, then city connections too
#verify forests at top part of minimap #define all rivers, add columns
#tile purchasing cost algorithm, less after 1st growth?
#select production projects each turn if they are no longer valid after all relevant actions. production applied at BEGINNING of turn. 1 turn left on NC and buiilt a city? it doesnt complete. right? restriced DURING turn too..
#figure out gpt formula: 1war and 1 worker =  1gpt, just 2 per after that? or era dependent? improvement cost?
#program all building effects, stoneworks, stable, verify aqeuduct, etc
#trade routes caravans ability almost done

#speed monitoring and efficiency*
#actually get the neural network functional

#minor:
#city hill tile yield values? think i got it. what about snow?
#luxes verify
#do we let the AI CHOOSE between pop and culture and free tech? yeah. whatever it wants. #does pop growth ancient ruins help expand borders?
#if we click outside grid, no invalid tile error msg...
#luxuries, also trading??
#era advancement
#golden age negative happiness?
#are embassies required to trade?
#show growth and prod status of indiviual cities, also visual tile improvements
#make ui nice food decimal rounding? #happiness, gold and culture are ints?
#verify science system overflow, display?
#pantheon system do NEW cities not auto get pantheons or do they?
#negative gold penalties check
#golden age verify tile gold also point req func, stacking?
#yield icons and toggle
#meeting people tech boost?
#wonders allowed toa by 42 pyramids by 52 else gold?
#great person slots
#multi civ? map importer? standard map size? 
#hover formulas? research agreements? sell buildings? delete units? FREE policies pretend we are poland?

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
	"Market": {"gold": 1, "gold_percentage": 0.25, "production_cost": 100, "techs_required": ["Currency"], "gold_cost": 500},
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
	"sheep":    {"food": 1},
	"cattle":   {"food": 1},
	"oasis":    {"food": 3, "gold": 1},
	"salt":     {"food": 1, "gold": 1, "luxury": True},
	"citrus":   {"food": 1, "gold": 1, "luxury": True},
	"incense":  {"gold": 2, "luxury": True},
	"spices":   {"gold": 2, "luxury": True},
	"silk":     {"gold": 2, "luxury": True},
	"silver":   {"gold": 2, "luxury": True},
	"gems":     {"gold": 3, "luxury": True},
	"cotton":   {"gold": 2, "luxury": True},
	"dyes":     {"gold": 2, "luxury": True},
	"truffles": {"gold": 2, "luxury": True},
	"ivory":    {"gold": 2, "luxury": True},
	"stone":    {"production": 1},
	"sugar":    {"gold": 2, "luxury": True},
	"bananas":  {"food": 1},
	"gold":     {"gold": 2, "luxury": True},
	"marble":   {"gold": 2, "luxury": True},
	"kailash":  {"faith": 6},  # also +2 happiness
	"fish":     {"food": 1},
	"whales":   {"food": 1, "gold": 1, "luxury": True},
	"crab":     {"gold": 2, "luxury": True},
	"pearls":   {"gold": 2, "luxury": True},
	"n":     {},
}

IMPROVEMENTS = {
	"Farm": { "tech_required": "Agriculture" },
	"Mine": { "tech_required": "Mining" },
	"Pasture": { "tech_required": "Animal Husbandry" },
	"Plantation": { "tech_required": "Calendar" },
	"Quarry": { "tech_required": "Masonry" },
	"Camp": { "tech_required": "Trapping" },
	"Trading Post": { "tech_required": "Guilds" },
	"Road": {"tech_required": "The Wheel"},
	"None": {},
}

TECHS = {
	"Agriculture": {"base_cost": 20, "prerequisites": []},
	"Pottery": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #allows granary and shrine
	"Animal Husbandry": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #reveals horses on map, allows caravans, pastures, +1 trade route
	"Archery": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #allows toa and archer
	"Mining": {"base_cost": 35, "prerequisites": ["Agriculture"]}, #mines and chopping forests

	"Sailing": {"base_cost": 55, "prerequisites": ["Pottery"], "era": "ancient"}, #extra trade route
	"Calendar": {"base_cost": 55, "prerequisites": ["Pottery"], "era": "ancient"}, #stone works and plantations
	"Writing": {"base_cost": 55, "prerequisites": ["Pottery"], "era": "ancient"}, #library
	"Trapping": {"base_cost": 55, "prerequisites": ["Animal Husbandry"], "era": "ancient"}, #camps and circus
	"The Wheel": {"base_cost": 55, "prerequisites": ["Animal Husbandry", "Archery"], "era": "ancient"}, #water mill and roads
	"Masonry": {"base_cost": 55, "prerequisites": ["Mining"], "era": "ancient"}, #pyramids, quarry, clear marsh
	"Bronze Working": {"base_cost": 55, "prerequisites": ["Mining"], "era": "ancient"}, #reveal iron, remove jungle

	"Optics": {"base_cost": 85, "prerequisites": ["Sailing"], "era": "classical"}, #lighthouse
	"Horseback Riding": {"base_cost": 105, "prerequisites": ["Trapping", "The Wheel"], "era": "classical"}, #stable, circus maximus
	"Mathematics": {"base_cost": 105, "prerequisites": ["The Wheel"], "era": "classical"}, #hanging gardens
	"Construction": {"base_cost": 105, "prerequisites": ["The Wheel", "Masonry"], "era": "classical"}, #colosseum, lumber mill

	"Philosophy": {"base_cost": 175, "prerequisites": ["Calendar", "Writing"], "era": "classical"}, #nat college, oracle
	"Drama and Poetry": {"base_cost": 175, "prerequisites": ["Writing"], "era": "classical"}, #writers guild
	"Currency": {"base_cost": 175, "prerequisites": ["Mathematics"], "era": "classical"}, #mint, market
	"Engineering": {"base_cost": 175, "prerequisites": ["Mathematics", "Construction"], "era": "classical"}, #aqueduct, bridge over river, extra trade route
	"Iron Working": {"base_cost": 175, "prerequisites": ["Bronze Working"], "era": "classical"}, #check cost

	"Theology": {"base_cost": 275, "prerequisites": ["Philosophy", "Drama and Poetry"], "era": "medieval"},
	"Civil Service": {"base_cost": 275, "prerequisites": ["Drama and Poetry", "Horseback Riding", "Currency"], "era": "medieval"}, #fresh water farms +1
	"Guilds": {"base_cost": 275, "prerequisites": ["Currency"], "era": "medieval"}, #trading posts
	"Metal Casting": {"base_cost": 275, "prerequisites": ["Engineering", "Iron Working"], "era": "medieval"}, #forge and workshop

	"Compass": {"base_cost": 375, "prerequisites": ["Optics"], "era": "medieval"}, #Extra trade route, check cost?
	"Education": {"base_cost": 485, "prerequisites": ["Theology", "Civil Service"], "era": "medieval"}, #university, allow research agreements
	"Chivalry": {"base_cost": 485, "prerequisites": ["Civil Service", "Guilds"], "era": "medieval"}, #mughal fort eh...
	"Machinery": {"base_cost": 485, "prerequisites": ["Guilds", "Engineering"], "era": "medieval"}, #ironworks, faster road movement
	"Physics": {"base_cost": 485, "prerequisites": ["Metal Casting"], "era": "medieval"}, #Notre Dame
	"Steel": {"base_cost": 485, "prerequisites": ["Metal Casting"], "era": "medieval"},

	"Astronomy": {"base_cost": 780, "prerequisites": ["Compass", "Education"], "era": "renaissance"}, #observatory
	"Acoustics": {"base_cost": 780, "prerequisites": ["Education"], "era": "renaissance"}, #sistine chapel
	"Banking": {"base_cost": 780, "prerequisites": ["Education", "Chivalry"], "era": "renaissance"}, #bank, forbidden palace, trade route
	"Printing Press": {"base_cost": 780, "prerequisites": ["Chivalry", "Machinery", "Physics"], "era": "renaissance"}, #zoo, leaning tower
	"Gunpowder": {"base_cost": 780, "prerequisites": ["Physics", "Steel"], "era": "renaissance"}
}

POLICIES = {
	"Tradition": {"desc": "Greatly increases rate of border growth. +3 Culture. Allows hanging gardens", "prerequisites": []}, #Implemented except border
	"Aristocracy": {"desc": "+1 happiness for every 10 citizens in a city. +15% wonder production", "prerequisites": ["Tradition"]}, #Implemented
	"Oligarchy": {"desc": "Units in cities cost no maintenance", "prerequisites": ["Tradition"]}, #Implemented
	"Legalism": {"desc": "First four cities get a FREE monument if they don't already have one", "prerequisites": ["Oligarchy"]}, #Implemented
	"Landed Elite": {"desc": "+2 food and +10% excess food in the capitol", "prerequisites": ["Legalism"]}, #Implemented
	"Monarchy": {"desc": "+1 gold and -1 unhappiness for every 2 citizens in the capital", "prerequisites": ["Legalism"]}, #Implemented
	#free aqueduct and 15% growth in first four cities upon completion #Implemented - aqeuduct retroactive?

	"Liberty": {"desc": "+1 culture per city. Allows pyramids", "prerequisites": []}, #Implemented
	"Republic": {"desc": "+1 production per city, 5% more building production", "prerequisites": ["Liberty"]}, #Implemented
	"Citizenship": {"desc": "Immediate worker, workers upgrade tiles 25% faster", "prerequisites": ["Liberty"]}, #Implemented
	"Collective Rule": {"desc": "Immediate settler, settlers cost 50% less.", "prerequisites": ["Republic"]}, #Implemented
	"Representation": {"desc": "Immediate golden age, culture cost from extra cities is 33% less", "prerequisites": ["Citizenship"]}, #Implemented
	"Meritocracy": {"desc": "+1 happiness for each city connected to capitol, also -5% unhappiness from citizens", "prerequisites": ["Citizenship"]}, #Implemented
	#great scientist/engineer upon completion

	"Patronage": {"desc": "City state rep is more resilient. Allows forbidden palace", "era": "Classical"}, #Implemented
	"Commerce": {"desc": "Gold yields up 25% in capital. Allows big ben", "era": "Medieval"}, #Implemented

	"Rationalism": {"desc": "Global science up 10%. Allows porcelain tower", "era": "Renaissance"} #Implemented
}

PANTHEONS = {
	"Oral Tradition": {"desc": "+1 Culture from Plantations"}, #Implemented
	"Goddess of Love": {"desc": "+1 Happiness from cities with Population of 6+"}, #Implemented
	"God of Craftsmen": {"desc": "+1 Production in cities with Population of 3+"}, #Implemented
	"Fertility Rites": {"desc": "+10% Growth in all cities"}, #Implemented
	"Goddess of the Hunt": {"desc": "+1 Food from Camps"}, #Implemented
	"God-King": {"desc": "+1 of each: Faith, Culture, Gold, Science, Production in Capital"}, #Implemented
	"Messenger of the Gods": {"desc": "2 Science in cities with a City Connection"}, #Implemented
	"Sacred Waters": {"desc": "+1 Happiness from cities on rivers"},
	"Sun God": {"desc": "+1 Food for each Bananas, Citrus, and Wheat resource"}, #Implemented
	"One with Nature": {"desc": "+4 faith from natural wonders"}, #Implemented for kailash only
	"Desert Folklore": {"desc": "+1 faith from each desert tile"}, #Implemented
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
	"p": {"name": "Plains", "food": 1, "production": 1},
	"g": {"name": "Grassland", "food": 2},
	"d": {"name": "Desert"},
	"t": {"name": "Tundra", "food": 1},
	"s": {"name": "Snow"},
	"c": {"name": "Coast", "food": 1},
	"o": {"name": "Ocean", "food": 1},
	"l": {"name": "Lake", "food": 2},
	"n": {"name": "None"},
}
