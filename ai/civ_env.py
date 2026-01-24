
#ai/civ_env.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import random

from engine import Engine
from engine import action_handler

Action = Dict[str, Any]
Obs = Dict[str, Any]


@dataclass
class EnvConfig:
    horizon_turns: int = 80
    # Also cap total legal actions per decision to avoid blowups
    max_legal_actions: int = 128
    max_move_actions_per_unit: int = 256

class CivEnv:
    """
    Headless RL wrapper around Engine.

    Reward is dense: reward_t = objective(s_{t+1}) - objective(s_t)
    Episode terminates when engine.turn > horizon_turns (turns start at 1).
    """

    def __init__(self, cfg: Optional[EnvConfig] = None):
        self.cfg = cfg or EnvConfig()
        self.engine: Optional[Engine] = None
        self._last_obj: float = 0.0

    # -------------------------
    # Core API
    # -------------------------
    def reset(self, seed: Optional[int] = None) -> Obs:
        if seed is not None:
            random.seed(seed)

        self.engine = Engine()
        self._last_obj = self._objective(self.engine)
        return self.engine.get_state()

    def legal_actions(self) -> List[Action]:
        assert self.engine is not None
        player = self.engine.current_player
    
        actions = self.engine.get_legal_actions(player)
    
        # Hard cap action space (just sample if somehow too large)
        if len(actions) > self.cfg.max_legal_actions:
            actions = random.sample(actions, self.cfg.max_legal_actions)
    
        return actions


    def step(self, action: Action) -> Tuple[Obs, float, bool, Dict[str, Any]]:
        assert self.engine is not None
    
        # Apply action
        result = action_handler.handle_action(
            self.engine,
            action["action"],
            action.get("data", {}),
            # Keep training headless; set True if you want replays from training later
            log_actions=False,
        )
    
        # HARD ASSERT: legal_actions() must only produce valid actions
        assert getattr(result, "success", True), f"Illegal action emitted: {action}"
    
        obs = self.engine.get_state()
    
        # Dense delta reward
        obj = self._objective(self.engine)
        reward = float(obj - self._last_obj)
        self._last_obj = obj
    
        done = bool(self.engine.turn > self.cfg.horizon_turns)
    
        info = {
            "success": True,
            "message": "",
            "turn": self.engine.turn,
            "objective": obj,
        }
        return obs, reward, done, info


    # -------------------------
    # Objective: food + science
    # -------------------------
    def _objective(self, engine: Engine) -> float:
        """
        Simple objective:
        - total science accrued
        - total population
        """
        p = engine.current_player
    
        science_accrued = float(getattr(p, "total_science_accrued", 0.0))
    
        pop = 0.0
        for c in p.cities:
            pop += float(getattr(c, "population", 0.0))
    
        return science_accrued + 20.0 * pop

    # -------------------------
    # Branching control
    # -------------------------
    def _reduce_move_actions(self, actions: List[Action]) -> List[Action]:
        assert self.engine is not None

        move_by_unit: Dict[int, List[Action]] = {}
        others: List[Action] = []

        for a in actions:
            if a.get("action") == "move_unit":
                uid = a.get("data", {}).get("unit_id")
                if uid is not None:
                    move_by_unit.setdefault(int(uid), []).append(a)
            else:
                others.append(a)

        reduced_moves: List[Action] = []

        for uid, acts in move_by_unit.items():
            scored: List[Tuple[float, Action]] = []
            for a in acts:
                to = a.get("data", {}).get("to")
                if not to or len(to) != 2:
                    continue
                q, r = int(to[0]), int(to[1])
                tile = self.engine.get_tile(q, r)
                # simple local desirability: yields
                s = float(
                    tile.food
                    + tile.production
                    + tile.science
                    + tile.gold
                    + tile.culture
                    + tile.faith
                )
                scored.append((s, a))

            scored.sort(key=lambda x: x[0], reverse=True)
            reduced_moves.extend([a for _, a in scored[: self.cfg.max_move_actions_per_unit]])

        return others + reduced_moves
