
#verify science system overflow, meeting people tech boost? civil service, iron and horses, bridges over rivers? machinery road movement
#purchase system finalize #purhcased things landing on same tile... stacking system?
#golden age verify tile gold also point req func, stacking?
#policies effects! finalize
#pantheon system finalize impllement
#verify starvation
#city connections check
#trade routes caravans
#negative gold penalties check
#program all building effects, stoneworks, stable, hanging gardens, lighthouse, aqeuduct, etc
#make ui nice food decimal rounding? or floor?

#tile improvement system #add dict improvement values, also adjacency bonuses for differnt tile types? flood plains? marsh?
#verify forests at top part of minimap #define all rivers, add columns
#settler cost situation
#citizen tile assignment choice system, #if city grows auto update the next worked tile to highest production tile then by gold
#tile purhcasing finalize
#happiness, gold and culture are ints?
#wonders allowed toa by 42 pyramids by 52 else gold?
#great person slots

#EVOLUTIONARY ALGORITHM TO TURN 121!!!!!! simpler gamestate, fitness func, and actions are best. pathfinding? forced TOA or nat college to test different builds?
##hover formulas? eh music selector? map importer? not just gandhi? standard map size? #reserarch agreements

#figure out gpt formula:
#1war and 1 worker =  1gpt
#embassies sim

#border growth algorithm and formula
#15 for first, NW ccotton 
#w/ tradition...

#turn 121 to beat:
#science 195, 6 turns till banking
#crop yield 200, 10 cities total
#86 hammers
#27 culture per turn
#900 + 97 gold per turn


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
        "E":  (1, 0),
        "NE": (0, -1),
    "NW": (-1, -1),
    "W":  (-1, 0),
    "SW": (-1, 1),
    "SE": (0, 1),
}

ODD_ROW_NEIGHBORS = {
        "E":  (1, 0),
        "NE": (1, -1),
    "NW": (0, -1),
    "W":  (-1, 0),
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

TERRAIN_TYPES =  {
        "p":    {"name": "plains", "food": 1, "production": 1},
        "g":    {"name": "grassland", "food": 2},
    "d":    {"name": "desert"},
    "t":    {"name": "tundra", "food": 1},
    "s":    {"name": "snow"},
    "c":     {"name": "coast", "food": 1},
    "o":     {"name": "ocean", "food": 1},
    "n":     {"name": "none"},
    "l":    {"name": "lake", "food": 2},
}

UNITS = {
        "Settler":    {"moves": 2, "hp": 100, "production_cost": 106, "gold_cost": 500},
        "Worker":    {"moves": 2, "production_cost": 70, "hp": 100, "gold_cost": 220},
    "Scout":    {"moves": 2, "production_cost": 25, "hp": 100, "gold_cost": 140},
    "Warrior":    {"moves": 2,  "production_cost": 40,"hp": 100, "gold_cost": 200},
    "Caravan":    {"moves": 0, "hp": 100, "techs_required": ["Animal Husbandry"], "production_cost": 75, "gold_cost": 390},
}

BUILDINGS = {
        "Palace":    {"science": 3, "production": 3, "gold": 3, "culture": 1},
    "Library":    {"maintenance": 1, "production_cost": 75, "techs_required": ["Writing"], "gold_cost": 400},
    "Shrine":    {"maintenance": 1, "faith": 1, "production_cost": 40, "techs_required": ["Pottery"], "gold_cost": 250},
    "Monument":    {"maintenance": 1,  "culture": 2, "production_cost": 40, "gold_cost": 280},
    "Monument (Free)":    {"culture": 2},
    "Granary":    {"maintenance": 1, "food": 2, "growth_percentage": 0.1, "production_cost": 60, "techs_required": ["Pottery"], "gold_cost": 340},
    "Water Mill":    {"maintenance": 2, "food": 2, "production": 1, "production_cost": 75, "techs_required": ["The Wheel"], "gold_cost": 400},
    "Temple of Artemis":    {"food": 1, "production_cost": 185, "techs_required": ["Archery"]},
    "Stone Works":    {"maintenance": 1, "production_cost": 75, "techs_required": ["Calendar"], "gold_cost": 320}, #city must have a quarry
    "Stable":    {"maintenance": 1, "production_cost": 100, "techs_required": ["Horseback Riding"], "gold_cost": 500},
    "Pyramids":    {"production_cost": 185, "techs_required": ["Masonry"], "policies_required": ["Liberty"]},
    "National College":    {"science": 3, "science_percentage": 0.5, "production_cost": 125, "techs_required": ["Philosophy"]}, #production_cost depends on cities "buildings_required_in_all_cities:": "Library"
    "Hanging Gardens":    {"food": 6, "culture": 1, "production_cost": 250, "techs_required": ["Mathematics"], "policies_required": ["Tradition"]}, #also grants a free garden!
    "Circus":    {"happiness": 2, "production_cost": 75, "techs_required": ["Trapping"], "gold_cost": 400}, #must have upgraded horses or ivory
    "Circus Maximus":    {"happiness": 5, "culture": 1, "production_cost": 125, "techs_required": ["Horseback Riding"]}, #must have upgraded horses or ivory, cost? also all colloseums
    "Lighthouse":    {"maintenance": 1, "production_cost": 75, "techs_required": ["Optics"], "gold_cost": 400},
    "Aqueduct":    {"maintenance": 1, "production_cost": 100, "techs_required": ["Engineering"], "gold_cost": 400},
    "Colosseum":    {"maintenance": 1, "happiness": 2, "production_cost": 100, "techs_required": ["Construction"], "gold_cost": 500},
    "University":    {"maintenance": 2, "production_cost": 160, "techs_required": ["Education"], "gold_cost": 660},
    "Market":    {"gold": 1, "production_cost": 100, "techs_required": ["Currency"], "gold_cost": 500},
    "Mint":    {"production_cost": 100, "techs_required": ["Currency"], "gold_cost": 500},
    "Artists' Guild":    {"maintenance": 1, "production_cost": 150, "techs_required": ["Guilds"]},
    "Writers' Guild":    {"maintenance": 1, "production_cost": 100, "techs_required": ["Drama and Poetry"]},
    "Workshop":    {"maintenance": 2, "production_cost": 120, "techs_required": ["Metal Casting"], "gold_cost": 580},
    "Observatory":    {"science_percentage": 0.5, "production_cost": 200, "techs_required": ["Astronomy"], "gold_cost": 780}, #must be built next to mountain
    "Garden":    {"maintenance": 1, "production_cost": 120, "techs_required": ["Theology"], "gold_cost": 580}, #City must border a source of fresh water
    "Forbidden Palace": {"production_cost": 2220, "techs_required": ["Banking"], "policies_required": ["Patronage"]}
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
    "silver":   {"gold": 2},
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
    "n":     {},
}

IMPROVEMENTS = {
        "farm": {"requires": "wheat", "bonus": {"food": 1}}, #2 food if fresh water with civil service
        "mine": {"requires": "hill", "bonus": {"hammers": 1}},
    "pasture": {"requires": ["cattle", "sheep", "horses"], "bonus": {"food": 1, "hammers": 1}},
    "plantation": {"requires": ["citrus", "incense", "spices", "dyes", "cotton", "sugar", "bananas"], "bonus": {"gold": 1}},
    "quarry": {"requires": ["stone", "marble"], "bonus": {"hammers": 1}},
    "camp": {"requires": ["ivory", "truffles", "deer"], "bonus": {"food": 1, "hammers": 1}},
    "trading post": {"requires": None, "bonus": {"food": 1, "hammers": 1}},
    "road": {"requires": None, "bonus": {"food": 1, "hammers": 1}},
    "none": {"requires": None, "bonus": {}},
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
    "Education": {"base_cost": 485, "prerequisites": ["Theology", "Civil Service"]}, #university
    "Chivalry": {"base_cost": 485, "prerequisites": ["Civil Service", "Guilds"]}, #mughal fort eh...
    "Machinery": {"base_cost": 485, "prerequisites": ["Guilds", "Engineering"]}, #ironworks, faster road movement
    "Physics": {"base_cost": 485, "prerequisites": ["Metal Casting"]}, #Notre Dame
    "Steel": {"base_cost": 485, "prerequisites": ["Metal Casting"]},

    "Astronomy": {"base_cost": 780, "prerequisites": ["Compass", "Education"]}, #observatory
    "Acoustics": {"base_cost": 780, "prerequisites": ["Education"]}, #sistine chapel
    "Banking": {"base_cost": 780, "prerequisites": ["Education", "Chivalry"]}, #bank, forbidden palace, trade route
    "Printing Press": {"base_cost": 780, "prerequisites": ["Chivalry", "Machinery", "Physics"]}, #zoo, leaning tower
    "Gunpowder": {"base_cost": 780, "prerequisites": ["Physics", "Steel"]}
}

POLICIES = {
        "Tradition": {"desc": "Greatly increases rate of border growth. +3 Culture. Allows hanging gardens", "prerequisites": []}, #Implemented except border
        "Aristocracy": {"desc": "+1 happiness for every 10 citizens in a city. +15% wonder production", "prerequisites": ["Tradition"]}, #local or global
    "Oligarchy": {"desc": "Units in cities cost no maintenance", "prerequisites": ["Tradition"]},
    "Legalism": {"desc": "First four cities get a FREE monument if they don't already have one", "prerequisites": ["Oligarchy"]}, #Implemented
    "Landed Elite": {"desc": "+2 food and +10% excess food in the capitol", "prerequisites": ["Legalism"]}, #Implemented
    "Monarchy": {"desc": "+1 gold and -1 unhappiness for every 2 citizens in the capital", "prerequisites": ["Legalism"]}, #local or global
    #free aqueduct and 15% growth in first four cities upon completion

    "Liberty": {"desc": "+1 culture per city. Allows pyramids", "prerequisites": []}, #Implemented
    "Republic": {"desc": "+1 production per city, 5% more building production", "prerequisites": ["Liberty"]}, #Implemented
    "Citizenship": {"desc": "Immediate worker, workers upgrade tiles 25% faster", "prerequisites": ["Liberty"]},
    "Collective Rule": {"desc": "Immediate settler, settlers cost 50% less.", "prerequisites": ["Republic"]},
    "Representation": {"desc": "Immediate golden age, culture cost from extra cities is 33% less", "prerequisites": ["Citizenship"]}, #Implemented
    "Meritocracy": {"desc": "+1 happiness for each city connected to capitol, also -5% unhappiness from citizens", "prerequisites": ["Citizenship"]}, #local or global
    #great scientist/engineer upon completion

    "Patronage": {"desc": "City state rep is more resilient. Allows forbidden palace", "prerequisites": ["classical era?"]}, #Implemented
    "Commerce": {"desc": "Gold yields up 25% in capitol. Allows big ben", "prerequisites": ["medieval era?"]}, #Implemented

    "Rationalism": {"desc": "Global science up 10%. Allows porcelain tower", "prerequisites": ["rennaisance era"]} #Implemented
}

PANTHEONS = { # do NEW cities not auto get pantheons or do they?
        "Oral Tradition": {"desc": " +1 Culture from Plantations"},
    "Goddess of Love": {"desc": " +1 Happiness from cities with Population of 6+"}, #local or global
    "God of Craftsmen": {"desc": "+1 Production in cities with Population of 3+"}, #Implemented
    "Fertility Rites": {"desc": "+10% Growth in all cities"}, #Implemented
    "Goddess of the Hunt": {"desc": "+1 Food from Camps"},
    "God-King": {"desc": "+1 of each: Faith, Culture, Gold, Science, Production in Capital"}, #Implemented
    "Messenger of the Gods": {"desc": "2 Science in cities with a City Connection"},
    "Sacred Waters": {"desc": "+1 Happiness from cities on rivers"}, #local or global
    "Sun God": {"desc": "+1 Food for each Bananas, Citrus, and Wheat resource"}, #Implemented
}