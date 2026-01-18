# Civ V Build Order Optimizer

**Author:** Avenos538
6/19/2025

A Civilization V strategy simulation with AI support for optimizing build orders.  
Features full UI, replay support, and JSON-based action scripting.

Todo: Add map import using OpenCV

## Installation
```bash
pip install requirements.txt



Civ-Evo: A Civ V Build Order Optimizer with Reinforcement Learning AI

This is a fan-made, non-commercial project inspired by Civilization V. All assets and mechanics are used for educational purposes only. I am not affiliated with Firaxis or 2K.

Hey all - I've been working on this side project and figured I'd share it here in case anyone's into AI, automation, or just wants to mess around with Civ V from a different angle.
Civ-Evo is a full simulation of Civilization V's systems up to the Renaissance era, where the AI doesn't follow hard-coded rules.
I built an reinforcement learning algorithm that runs the game over and over, tweaking its own strategies to maximize yields - food, hammers, and science - over a specified number of turns.
You can throw it a hex map, and it'll play through thousands of games until it figures out what works. City placements, build orders, tile assignments, etc.


What's missing (for now):
No barbarians, multiple players, or combat mechanics
All RNG has been removed (Ancient ruins bonuses are CHOSEN, border expansion is now deterministic, city-state worker steals are simulated at specified intervals, etc.)

I built this mostly out of curiosity - to see if an algorithm could learn how to "play Civ" instead of the purely heuristic driven built-in AI.
I'm still working on improving performance and adding more game mechanics.
That said, it consistently achieves better food, science, and hammers than I can on any map I give it.

Examples:

If anyone's interested in contributing, testing, or just curious how it works, here is the code:
GitHub: github.com/Avenos538/civ-evo

Would love feedback, suggestions, or anyone interested in helping evolve it further.