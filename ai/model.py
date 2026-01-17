# ai/model.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn


# -----------------------------
# Feature hashing encoder
# -----------------------------
class FeatureHasher:
	"""
	Encodes nested dict/list objects (obs/state and action dicts) into fixed-size vectors.

	This avoids writing a giant hand-coded encoder on day 1. It is deterministic and fast.
	"""
	def __init__(self, dim: int = 4096):
		self.dim = int(dim)

	def encode(self, obj: Any, prefix: str) -> np.ndarray:
		v = np.zeros(self.dim, dtype=np.float32)
		self._accumulate(v, obj, prefix=prefix)
		return v

	def encode_state(self, state: Dict[str, Any]) -> np.ndarray:
		return self.encode(state, prefix="s")

	def encode_action(self, action: Dict[str, Any]) -> np.ndarray:
		return self.encode(action, prefix="a")

	def _h(self, s: str) -> int:
		# Stable 32-bit FNV-1a (avoid Python's randomized hash)
		h = 2166136261
		for ch in s:
			h ^= ord(ch)
			h = (h * 16777619) & 0xFFFFFFFF
		return int(h % self.dim)

	def _add(self, v: np.ndarray, key: str, value: float):
		v[self._h(key)] += float(value)

	def _accumulate(self, v: np.ndarray, x: Any, prefix: str):
		if x is None:
			self._add(v, f"{prefix}=None", 1.0)
			return

		if isinstance(x, bool):
			self._add(v, f"{prefix}={int(x)}", 1.0)
			return

		if isinstance(x, (int, float, np.number)):
			self._add(v, prefix, float(x))
			return

		if isinstance(x, str):
			self._add(v, f"{prefix}={x}", 1.0)
			return

		if isinstance(x, dict):
			for k, vv in x.items():
				self._accumulate(v, vv, f"{prefix}.{k}")
			return

		if isinstance(x, (list, tuple)):
			# keep bounded to avoid huge loops
			N = 128
			for i, vv in enumerate(x[:N]):
				self._accumulate(v, vv, f"{prefix}[{i}]")
			if len(x) > N:
				self._add(v, f"{prefix}.trunc", 1.0)
			return

		# fallback: tag the type
		self._add(v, f"{prefix}.type={type(x).__name__}", 1.0)


# -----------------------------
# Model
# -----------------------------
@dataclass
class ModelConfig:
	feature_dim: int = 4096
	hidden1: int = 512
	hidden2: int = 256


class Model(nn.Module):
	"""
	Fresh model for Civ decision-making:

	- value(state) -> scalar
	- score(state, action) -> scalar logit (used to choose among legal actions)

	This matches how we actually need to act/train with variable-sized legal action sets.
	"""
	def __init__(self, cfg: Optional[ModelConfig] = None):
		super().__init__()
		self.cfg = cfg or ModelConfig()

		d = self.cfg.feature_dim

		self.value_net = nn.Sequential(
	        nn.Linear(d, self.cfg.hidden1),
	    nn.Tanh(),
	    nn.Linear(self.cfg.hidden1, self.cfg.hidden2),
	    nn.Tanh(),
	    nn.Linear(self.cfg.hidden2, 1),
	)

		self.action_net = nn.Sequential(
	        nn.Linear(d * 2, self.cfg.hidden1),
	    nn.Tanh(),
	    nn.Linear(self.cfg.hidden1, self.cfg.hidden2),
	    nn.Tanh(),
	    nn.Linear(self.cfg.hidden2, 1),
	)

		# encoder instance for convenience (keeps main/agent code simple)
		self.fe = FeatureHasher(dim=d)

	def value(self, s: torch.Tensor) -> torch.Tensor:
		# s: [B, D]
		return self.value_net(s).squeeze(-1)

	def score(self, s: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
		# s: [B, D], a: [B, D]
		x = torch.cat([s, a], dim=-1)
		return self.action_net(x).squeeze(-1)

	@torch.no_grad()
	def score_legal_actions(
            self,
        state_vec: np.ndarray,
        action_vecs: np.ndarray,
        device: torch.device,
        batch: int = 512,
        ) -> np.ndarray:
		"""
		state_vec: [D]
		action_vecs: [N, D]
		returns logits: [N]
		"""
		self.eval()
		s = torch.from_numpy(state_vec).to(device).unsqueeze(0)  # [1, D]
		logits_out: List[np.ndarray] = []

		for i in range(0, action_vecs.shape[0], batch):
			a_np = action_vecs[i : i + batch]
			a = torch.from_numpy(a_np).to(device)
			s_rep = s.repeat(a.shape[0], 1)
			logits = self.score(s_rep, a).detach().cpu().numpy()
			logits_out.append(logits)

		return np.concatenate(logits_out, axis=0)
