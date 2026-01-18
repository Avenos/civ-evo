
# ai/train_ppo.py

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, Tuple
import numpy as np
from .civ_env import CivEnv, EnvConfig
import torch
import torch.nn as nn
import torch.optim as optim

Action = Dict[str, Any]
Obs = Dict[str, Any]


# -----------------------------
# Feature hashing (fresh encoder)
# -----------------------------
class FeatureHasher:
    def __init__(self, dim: int = 4096):
        self.dim = int(dim)

    def obs_vec(self, obs: Obs) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        self._accumulate(v, obs, prefix="obs")
        return v

    def act_vec(self, act: Action) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        self._accumulate(v, act, prefix="act")
        return v

    def _h(self, s: str) -> int:
        h = 2166136261
        for ch in s:
            h ^= ord(ch)
            h *= 16777619
            h &= 0xFFFFFFFF
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
            N = 128
            for i, vv in enumerate(x[:N]):
                self._accumulate(v, vv, f"{prefix}[{i}]")
            if len(x) > N:
                self._add(v, f"{prefix}.trunc", 1.0)
            return
        self._add(v, f"{prefix}.type={type(x).__name__}", 1.0)


# -----------------------------
# Networks: value(state) and logit(state, action)
# -----------------------------
class ValueNet(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, 512),
            nn.Tanh(),
            nn.Linear(512, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
        )

    def forward(self, s: torch.Tensor) -> torch.Tensor:
        return self.net(s).squeeze(-1)


class ActionScoreNet(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim * 2, 512),
            nn.Tanh(),
            nn.Linear(512, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
        )

    def forward(self, s: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        x = torch.cat([s, a], dim=-1)
        return self.net(x).squeeze(-1)


# -----------------------------
# PPO bits
# -----------------------------
@dataclass
class PPOConfig:
    seed: int = 0
    feature_dim: int = 4096

    rollout_steps: int = 2048
    gamma: float = 0.99
    gae_lambda: float = 0.95

    lr: float = 3e-4
    train_epochs: int = 6
    minibatch_size: int = 256

    clip_ratio: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 1.0

    iters: int = 200


def set_seeds(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def softmax_sample(logits: np.ndarray) -> Tuple[int, float]:
    m = float(np.max(logits))
    ex = np.exp(logits - m)
    p = ex / np.sum(ex)
    idx = int(np.random.choice(len(p), p=p))
    logp = float(np.log(p[idx] + 1e-12))
    return idx, logp


def compute_gae(rewards, dones, values, last_value, gamma, lam):
    T = len(rewards)
    adv = np.zeros(T, dtype=np.float32)
    last_gae = 0.0
    for t in reversed(range(T)):
        next_nonterminal = 1.0 - float(dones[t])
        next_value = last_value if t == T - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value * next_nonterminal - values[t]
        last_gae = delta + gamma * lam * next_nonterminal * last_gae
        adv[t] = last_gae
    returns = adv + values
    return adv, returns


def _fitness_from_obs(obs: Obs) -> float:
    if not isinstance(obs, dict):
        return 0.0

    p = obs.get("player", {})
    cities = obs.get("cities", [])

    science_accrued = float(p.get("total_science_accrued", 0.0))

    pop = 0.0
    for c in cities:
        pop += float(c.get("population", 0.0))

    return science_accrued + 20.0 * pop



def train_ppo():
    ppo = PPOConfig()
    set_seeds(ppo.seed)

    env = CivEnv(
        EnvConfig(
            horizon_turns=75
        )
    )
    fe = FeatureHasher(dim=ppo.feature_dim)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    value_net = ValueNet(dim=ppo.feature_dim).to(device)
    act_net = ActionScoreNet(dim=ppo.feature_dim).to(device)
    optimizer = optim.Adam(list(value_net.parameters()) + list(act_net.parameters()), lr=ppo.lr)

    # Rollout buffers
    S = np.zeros((ppo.rollout_steps, ppo.feature_dim), dtype=np.float32)
    A = np.zeros((ppo.rollout_steps, ppo.feature_dim), dtype=np.float32)
    logp_old = np.zeros((ppo.rollout_steps,), dtype=np.float32)
    rewards = np.zeros((ppo.rollout_steps,), dtype=np.float32)
    dones = np.zeros((ppo.rollout_steps,), dtype=np.float32)
    values = np.zeros((ppo.rollout_steps,), dtype=np.float32)

    obs = env.reset(seed=ppo.seed)
    episodes = 0

    for it in range(1, ppo.iters + 1):
        # One header line per training iteration (what you asked for)
        print(f"\nStarting training loop {it}/{ppo.iters}")

        # -------- Rollout --------
        for t in range(ppo.rollout_steps):
            s_vec = fe.obs_vec(obs)

            legal = env.legal_actions()
            if not legal:
                # force a legal-ish transition
                obs, _, _, _ = env.step({"action": "end_turn", "data": {}})
                legal = env.legal_actions()

            a_vecs = np.stack([fe.act_vec(a) for a in legal], axis=0)

            with torch.no_grad():
                s_t = torch.from_numpy(s_vec).to(device).unsqueeze(0)
                v = value_net(s_t).cpu().item()
                values[t] = float(v)

                s_rep = s_t.repeat(a_vecs.shape[0], 1)
                a_t = torch.from_numpy(a_vecs).to(device)
                logits_t = act_net(s_rep, a_t).cpu().numpy()

            idx, lp = softmax_sample(logits_t)
            act = legal[idx]

            next_obs, r, done, info = env.step(act)

            # store
            S[t] = s_vec
            A[t] = a_vecs[idx]
            logp_old[t] = lp
            rewards[t] = float(r)
            dones[t] = 1.0 if done else 0.0

            obs = next_obs

            # ----- YOUR LOG FORMAT -----
            # "turn" is best-effort: prefer env turn, then info['turn'], else derive from t.
            turn = None
            if isinstance(info, dict) and "turn" in info:
                try:
                    turn = int(info["turn"])
                except Exception:
                    turn = None
            if turn is None and hasattr(env, "turn"):
                try:
                    turn = int(getattr(env, "turn"))
                except Exception:
                    turn = None
            if turn is None:
                # derive something sensible
                turn = 1 + (t % max(1, env.cfg.horizon_turns))

            # fitness: best-effort from obs (or you can replace with your exact function)
            fitness = _fitness_from_obs(obs)

            # one line per turn with fitness value
            print(
                f"  turn {turn:03d}/{env.cfg.horizon_turns} "
                f"action={act['action']} "
                f"data={act.get('data', {})} "
                f"fitness={fitness:,.3f}"
            )


            if done:
                obs = env.reset()
                episodes += 1

        # Bootstrap value for last obs
        with torch.no_grad():
            last_v = value_net(
                torch.from_numpy(fe.obs_vec(obs)).to(device).unsqueeze(0)
            ).cpu().item()

        adv, ret = compute_gae(
            rewards=rewards,
            dones=dones,
            values=values,
            last_value=float(last_v),
            gamma=ppo.gamma,
            lam=ppo.gae_lambda,
        )
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)

        # -------- Train --------
        idxs = np.arange(ppo.rollout_steps)
        for _ in range(ppo.train_epochs):
            np.random.shuffle(idxs)
            for start in range(0, ppo.rollout_steps, ppo.minibatch_size):
                mb = idxs[start : start + ppo.minibatch_size]

                s_mb = torch.from_numpy(S[mb]).to(device)
                a_mb = torch.from_numpy(A[mb]).to(device)
                logp_old_mb = torch.from_numpy(logp_old[mb]).to(device)
                adv_mb = torch.from_numpy(adv[mb]).to(device)
                ret_mb = torch.from_numpy(ret[mb]).to(device)

                logits = act_net(s_mb, a_mb)
                logp_new = -torch.nn.functional.softplus(-logits)  # log(sigmoid(logits))

                ratio = torch.exp(logp_new - logp_old_mb)
                clipped = torch.clamp(ratio, 1.0 - ppo.clip_ratio, 1.0 + ppo.clip_ratio)
                policy_loss = -(torch.min(ratio * adv_mb, clipped * adv_mb)).mean()

                v = value_net(s_mb)
                value_loss = ((v - ret_mb) ** 2).mean()

                entropy = torch.nn.functional.softplus(-logits).mean()

                loss = policy_loss + ppo.value_coef * value_loss - ppo.entropy_coef * entropy

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(
                    list(value_net.parameters()) + list(act_net.parameters()),
                    ppo.max_grad_norm,
                )
                optimizer.step()

        # One compact end-of-iter summary (optional, but useful)
        avg_r = float(np.mean(rewards))
        print(f"End loop {it}/{ppo.iters}  avg_step_reward={avg_r:+.4f}  episodes={episodes}")

    print("\nDone.")
