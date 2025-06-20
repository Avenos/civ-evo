#possible actions:
#move a unit to a tile
#start production in a city
#purchase a tile or unit or building
#settle a city
#choose a tech
#choose social policy or pantheon
#choose tiles worked by cities
#perform a worker chop or improvment
#assign a trade route

def handle_action(engine, action_type, data):
    """
    Handles a single action applied to the engine.
    Returns (success: bool, error_msg: str or None)
    """

    if action_type == "move_unit":
        unit = engine.get_unit_by_id(data["unit_id"])
        to_q, to_r = data["to"]
        if not unit:
            return False, "Unit not found"
        from_tile = engine.tiles[unit.q][unit.r]
        to_tile = engine.tiles[to_q][to_r]
        result = unit.move_to(from_tile, to_tile)
        if result is not True:
            # result is an error message string if move failed
            return False, result
        return True, None

    elif action_type == "found_city":
        unit = engine.get_unit_by_id(data["unit_id"])
        if not unit:
            return False, "Unit not found for founding city"
        success, error = engine.current_player.found_city(unit, engine)
        if not success:
            return False, error
        return True, None

    elif action_type == "start_project":
        city = engine.get_city_by_id(data["city_id"])
        if not city:
            return False, "City not found for production choice"

        # Find the project object by name
        project_name = data["project_name"]
        project = next((p for p in city.production_system.projects if p.name == project_name), None)

        if not project:
            return False, f"Project '{project_name}' not found in city's project list"

        success, error = city.production_system.start_project(project)
        if not success:
            return False, error

        return True, None
    
    elif action_type == "set_research":
            success = engine.current_player.science_system.set_current_research(data["tech_name"])
            if not success:
                return False, f"Cannot research {data['tech_name']}"
            return True, None
        

    elif action_type == "end_turn": #called here or up above?
        success, error_msg = engine.end_turn()
        if not success:
            return False, error_msg
        return True, None

    else:
        return False, f"Unknown action type: {action_type}"

    #elif action_type == "purchase_unit":
        #city = engine.get_city_by_id(data["city_id"])
        #if city:
            #city.purchase_unit(data["name"], engine.current_player)

    #elif action_type == "select_policy":
        #policy = data["policy"]
        #engine.current_player.choose_policy(policy, engine)

    #elif action_type == "select_tech":
        #tech_name = data["tech"]
        #engine.current_player.science_system.set_current_research(tech_name)

