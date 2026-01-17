from rl.civ_env import CivEnv, EnvConfig
import random

env = CivEnv(EnvConfig(horizon_turns=10))
obs = env.reset(seed=0)

total_r = 0.0
done = False
while not done:
    legal = env.legal_actions()
    a = random.choice(legal)
    obs, r, done, info = env.step(a)
    total_r += r

print("done", info["turn"], "total_reward", total_r, "final_objective", info["objective"])
