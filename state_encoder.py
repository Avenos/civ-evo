import torch

# === Configurable constants ===
MAX_CITIES = 10
MAX_UNITS = 20
MAX_POLICIES = 50
MAX_TECHS = 50
MAX_TILES_Q = 10  # Grid width
MAX_TILES_R = 10  # Grid height

# --- Dummy mappings for categorical values ---
def one_hot(index, size):
	vec = [0.0] * size
	if index is not None and 0 <= index < size:
		vec[index] = 1.0
	return vec

PANTHEON_LIST = [
        None, "God of War", "God of the Sea", "Earth Mother", "Fertility Rites",
    "Ancestor Worship", "Sun God", "Stone Circles", "Divine Spark", "Sacred Path"
]
PANTHEON_INDEX = {name: i for i, name in enumerate(PANTHEON_LIST)}

def pantheon_to_index(name):
	return PANTHEON_INDEX.get(name, 0)

def name_to_index(name, name_list, max_size):
	try:
		return name_list.index(name)
	except ValueError:
		if len(name_list) < max_size:
			name_list.append(name)
			return len(name_list) - 1
		return 0  # fallback

# Global name banks
policy_bank = []
tech_bank = []
unit_bank = []
building_bank = []
resource_bank = []
terrain_bank = []
improvement_bank = []

def encode_game_state(state):
	features = []

	# --- Global turn ---
	features.append(float(state["turn"]))

	player = state["player"]

	# --- Player economic stats ---
	features.extend([
            float(player["gold"]),
        float(player["gold_per_turn"]),
        float(player["culture"]),
        float(player["culture_per_turn"]),
        float(player["total_science_accrued"]),
        float(player["science_per_turn"]),
        float(player["faith"]),
        float(player["faith_per_turn"]),
    ])

	# --- Pantheon ---
	features.extend(one_hot(pantheon_to_index(player["pantheon"]), len(PANTHEON_LIST)))

	# --- Policies ---
	policy_vec = [0.0] * MAX_POLICIES
	for p in player["unlocked_policies"]:
		idx = name_to_index(p, policy_bank, MAX_POLICIES)
		policy_vec[idx] = 1.0
	features.extend(policy_vec)

	# --- Techs ---
	tech_vec = [0.0] * MAX_TECHS
	for t in player["unlocked_techs"]:
		idx = name_to_index(t, tech_bank, MAX_TECHS)
		tech_vec[idx] = 1.0
	features.extend(tech_vec)

	# --- Current research progress ---
	features.append(float(player.get("current_research_progress", 0.0)))

	# --- Units ---
	for i in range(MAX_UNITS):
		if i < len(state["units"]):
			u = state["units"][i]
			features.extend([
	            float(u["q"]),
	        float(u["r"]),
	        float(u["moves_left"]),
	    ])
			features.extend(one_hot(name_to_index(u["name"], unit_bank, 50), 50))
		else:
			features.extend([0.0, 0.0, 0.0] + [0.0] * 50)

	# --- Cities ---
	for i in range(MAX_CITIES):
		if i < len(state["cities"]):
			c = state["cities"][i]
			features.extend([
	            float(c["q"]),
	        float(c["r"]),
	        float(c["population"]),
	        float(c["food"]),
	        float(c["production"]),
	        float(c["science"]),
	        float(c["culture"]),
	        float(c["faith"]),
	        float(c.get("current_production_progress", 0.0)),
	    ])
		else:
			features.extend([0.0] * 9)

	# --- Tiles (sparse, optional, expensive!) ---
	for q in range(min(len(state["tiles"]), MAX_TILES_Q)):
		col = state["tiles"][q]
		for r in range(min(len(col), MAX_TILES_R)):
			t = col[r]
			features.extend([
	            float(t["q"]), float(t["r"]),
	        float(name_to_index(t["terrain_type"], terrain_bank, 20)),
	        float(name_to_index(t.get("resource"), resource_bank, 20)),
	        float(t["food"]), float(t["production"]), float(t["science"]),
	        float(t["gold"]), float(t["culture"]), float(t["faith"]),
	        float(name_to_index(t.get("improvement"), improvement_bank, 20)),
	    ])
		# Pad rest of column if needed
		for _ in range(MAX_TILES_R - len(col)):
			features.extend([0.0] * 11)
	# Pad rest of map if needed
	for _ in range(MAX_TILES_Q - len(state["tiles"])):
		features.extend([0.0] * (MAX_TILES_R * 11))

	# === Final tensor ===
	return torch.tensor(features, dtype=torch.float32)
