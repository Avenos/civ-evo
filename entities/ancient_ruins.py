
class AncientRuins:
	RUINS_EFFECTS = {
		1: "Gain 75 gold",
		2: "Gain 20 culture", #only possibly triggers AFTER turn 20
		3: "Gain 1 pop in nearest city",
		4: "Free tech",
		#5: "Gain 20 or 60?? faith ONLY after turn 20",
	}

	def __init__(self, effect_id):
		self.effect_id = effect_id
		self.description = self.RUINS_EFFECTS.get(effect_id, "Unknown effect")

	def trigger(self, player, tile, chosen_effect_id=None, chosen_tech=None):
		effect_id = chosen_effect_id if chosen_effect_id is not None else self.effect_id

		valid_effects = {1,2,3,4}

		if effect_id not in valid_effects:
			raise ValueError(f"Invalid chosen effect ID: {effect_id}")

		if effect_id == 1:
			player.gold += 75

		elif effect_id == 2:
			player.culture += 20

		elif effect_id == 3:
			if not player.cities:
				return
			cities_with_dist = [(hex_distance(tile.q, tile.r, city.q, city.r), city) for city in player.cities]
			cities_with_dist.sort(key=lambda x: x[0])
			min_dist = cities_with_dist[0][0]
			closest_cities = [c for d, c in cities_with_dist if d == min_dist]

			city_to_grow = None
			for city in player.cities:
				if city in closest_cities:
					city_to_grow = city
					break

			if city_to_grow:
				city_to_grow.population += 1
				city_to_grow.update_worked_tiles(player.game)

		elif effect_id == 4:
			unlocked_techs = player.science_system.get_unlocked_names()
			eligible_techs = []
			for tech_name in player.science_system.techs:
				tech = player.science_system.techs[tech_name]
				if tech_name not in unlocked_techs and tech.can_research(unlocked_techs):
					eligible_techs.append(tech_name)

			if not eligible_techs:
				return

			# If player didn't specify a tech, pick first eligible by default? or MUST they choose?
			tech_to_complete = chosen_tech if chosen_tech in eligible_techs else eligible_techs[0]

			player.science_system.complete_tech(tech_to_complete)
			player.science_system.set_current_research(None)
			player.game.show_message(f"Ancient Ruins completed tech: {tech_to_complete}", 90)

		#pantheon after t20?

		tile.ancient_ruin = None
