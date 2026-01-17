# ai/smart_agent.py
from __future__ import annotations

import math
import random
from typing import Any, Dict, List

import numpy as np
import torch

from engine import action_handler
from ai.model import Model


Action = Dict[str, Any]


class SmartAgent:
    """
    Runs a game using a trained (or random-initialized) Model.
    This is for DEBUG / PLAY, not training.
    """

    def __init__(
        self,
        model: Model,
        device: torch.device,
        max_move_actions_per_unit: int = 6,
        temperature: float = 1.0,
        deterministic: bool = False,
        verbose: bool = True,
    ):
        self.model = model
        self.device = device
        self.max_move_actions_per_unit = max_move_actions_per_unit
        self.temperature = float(temperature)
        self.deterministic = deterministic
        self.verbose = verbose

    def run(self, engine):
        """
        Main agent loop. Called from your main().
        """
        self.model.eval()

        while engine.turn < 100 :
            player = engine.current_player

            state = engine.get_state()
            legal = engine.get_legal_actions(player)

            if not legal:
                action_handler.handle_action(engine, "end_turn", {})
                continue

            legal = self._reduce_move_actions(engine, legal)

            action = self._select_action(state, legal)

            if self.verbose:
                print(
                    f"[AI] turn={engine.turn:03d} "
                    f"actions={len(legal):3d} "
                    f"chosen={action['action']} {action.get('data', {})}"
                )

            action_handler.handle_action(
                engine,
                action["action"],
                action.get("data", {}),
            )

    # --------------------------------------------------
    # Action selection
    # --------------------------------------------------
    def _select_action(self, state: Dict[str, Any], legal: List[Action]) -> Action:
        """
        Score all legal actions and choose one.
        """
        # Encode state
        s_vec = self.model.fe.encode_state(state)

        # Encode actions
        a_vecs = np.stack(
            [self.model.fe.encode_action(a) for a in legal],
            axis=0,
        )

        # Score
        logits = self.model.score_legal_actions(
            state_vec=s_vec,
            action_vecs=a_vecs,
            device=self.device,
        )

        if self.deterministic:
            idx = int(np.argmax(logits))
            return legal[idx]

        # Softmax sampling (with temperature)
        logits = logits / max(self.temperature, 1e-6)
        logits = logits - np.max(logits)  # stability
        probs = np.exp(logits)
        probs /= np.sum(probs)

        idx = int(np.random.choice(len(legal), p=probs))
        return legal[idx]

    # --------------------------------------------------
    # Movement branching control
    # --------------------------------------------------
    def _reduce_move_actions(self, engine, actions: List[Action]) -> List[Action]:
        """
        Keep all non-move actions.
        For move_unit actions, keep top-K per unit based on destination tile yields.
        """
        move_actions: Dict[Any, List[Action]] = {}
        others: List[Action] = []

        for a in actions:
            if a.get("action") == "move_unit":
                uid = a.get("data", {}).get("unit_id")
                if uid is not None:
                    move_actions.setdefault(uid, []).append(a)
            else:
                others.append(a)

        reduced_moves: List[Action] = []

        for uid, acts in move_actions.items():
            scored = []
            for a in acts:
                to = a.get("data", {}).get("to")
                if not to or len(to) != 2:
                    continue
                q, r = to
                tile = engine.get_tile(q, r)
                if tile is None:
                    continue

                score = (
                    tile.food
                    + tile.production
                    + tile.science
                    + tile.gold
                    + tile.culture
                )
                scored.append((score, a))

            scored.sort(key=lambda x: x[0], reverse=True)
            for _, a in scored[: self.max_move_actions_per_unit]:
                reduced_moves.append(a)

        return others + reduced_moves
