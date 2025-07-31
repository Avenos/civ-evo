
#here is state_encoder.py - remember, we are just feeding you context for now. lots of files. I do NOT want you to do any actual analysis yet, I will let you know when I want that. just acknowledge that this file is now in your brain and wait for the next one.

import torch

class StateEncoder:
	MAX_CITIES = 12
	MAX_UNITS = 30
	MAX_POLICIES = 25
	MAX_TECHS = 50
	MAX_TILES_Q = 23  # Grid width
	MAX_TILES_R = 23  # Grid height

	PANTHEON_LIST = [
		None, "God of War", "God of the Sea", "Earth Mother", "Fertility Rites", "Sun God", "Stone Circles", "Sacred Path"
	]
	PANTHEON_INDEX = {name: i for i, name in enumerate(PANTHEON_LIST)}

	# Global name banks as class attributes
	policy_bank = []
	tech_bank = []
	unit_bank = []
	building_bank = []
	resource_bank = []
	terrain_bank = []
	improvement_bank = []

	@staticmethod
	def one_hot(index, size):
		vec = [0.0] * size
		if index is not None and 0 <= index < size:
			vec[index] = 1.0
		return vec

	@classmethod
	def pantheon_to_index(cls, name):
		return cls.PANTHEON_INDEX.get(name, 0)

	@classmethod
	def name_to_index(cls, name, name_list, max_size):
		try:
			return name_list.index(name)
		except ValueError:
			if len(name_list) < max_size:
				name_list.append(name)
				return len(name_list) - 1
			return 0  # fallback

	def encode_game_state(self, state):
		features = []
	
		# --- Global turn ---
		features.append(int(state.get("turn", 0.0)))
	
		player = state.get("player", {})
	
		# --- Player economic stats ---
		features.extend([
		    float(player.get("gold", 0.0)),
		float(player.get("gold_per_turn", 0.0)),
		float(player.get("culture", 0.0)),
		float(player.get("culture_per_turn", 0.0)),
		float(player.get("total_science_accrued", 0.0)),
		float(player.get("science_per_turn", 0.0)),
		float(player.get("faith", 0.0)),
		float(player.get("faith_per_turn", 0.0)),
	    ])
	
		# --- Pantheon (one-hot) ---
		pantheon_index = self.pantheon_to_index(player.get("pantheon", ""))
		features.extend(self.one_hot(pantheon_index, len(self.PANTHEON_LIST)))
	
		# --- Policies (one-hot) ---
		policy_vec = [0.0] * self.MAX_POLICIES
		for p in player.get("unlocked_policies", []):
			idx = self.name_to_index(p, self.policy_bank, self.MAX_POLICIES)
			if 0 <= idx < self.MAX_POLICIES:
				policy_vec[idx] = 1.0
		features.extend(policy_vec)
	
		# --- Techs (one-hot) ---
		tech_vec = [0.0] * self.MAX_TECHS
		for t in player.get("unlocked_techs", []):
			idx = self.name_to_index(t, self.tech_bank, self.MAX_TECHS)
			if 0 <= idx < self.MAX_TECHS:
				tech_vec[idx] = 1.0
		features.extend(tech_vec)
	
		# --- Current research progress ---
		features.append(float(player.get("current_research_progress", 0.0)))
	
		# --- Units ---
		for i in range(self.MAX_UNITS):
			if i < len(state.get("units", [])):
				u = state["units"][i]
				features.extend([
			    int(u.get("q", 0.0)),
			int(u.get("r", 0.0)),
			int(u.get("moves_left", 0.0)),
		    ])
				unit_idx = self.name_to_index(u.get("name", ""), self.unit_bank, 50)
				features.extend(self.one_hot(unit_idx, 50))
			else:
				features.extend([0.0, 0.0, 0.0] + [0.0] * 50)
	
		# --- Cities ---
		for i in range(self.MAX_CITIES):
			if i < len(state.get("cities", [])):
				c = state["cities"][i]
				features.extend([
			    int(c.get("q", 0.0)),
			int(c.get("r", 0.0)),
			int(c.get("population", 0.0)),
			float(c.get("food", 0.0)),
			float(c.get("production", 0.0)),
			float(c.get("science", 0.0)),
			float(c.get("culture", 0.0)),
			float(c.get("faith", 0.0)),
			float(c.get("current_production_progress", 0.0)),
		    ])
			else:
				features.extend([0.0] * 9)
	
		# --- Tiles ---
		tiles = state.get("tiles", [])
		for q in range(self.MAX_TILES_Q):
			if q < len(tiles):
				col = tiles[q]
			else:
				col = []
	
			for r in range(self.MAX_TILES_R):
				if r < len(col):
					t = col[r]
					features.extend([
				float(t.get("q", 0.0)),
			    float(t.get("r", 0.0)),
			    float(self.name_to_index(t.get("terrain_type", ""), self.terrain_bank, 20)),
			    float(self.name_to_index(t.get("resource", ""), self.resource_bank, 20)),
			    float(t.get("food", 0.0)),
			    float(t.get("production", 0.0)),
			    float(t.get("science", 0.0)),
			    float(t.get("gold", 0.0)),
			    float(t.get("culture", 0.0)),
			    float(t.get("faith", 0.0)),
			    float(self.name_to_index(t.get("improvement", ""), self.improvement_bank, 20)),
			])
				else:
					features.extend([0.0] * 11)
	
		return torch.tensor(features, dtype=torch.float32)
