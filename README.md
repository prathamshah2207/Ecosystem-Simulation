# 🌱 EcoSim — Terminal Ecosystem Simulator

A lightweight, terminal-based ecosystem where **rabbits** wander, eat grass, burn energy, reproduce, and (sometimes) perish. Features **per-tile capacity**, **movement conflict resolution** (custom lottery), **energy dynamics**, **grass regrowth**, and a clean **curses UI** with live stats.

---

## 📖 Overview

- Discrete 2D grid with **grass timers** and **free slots** per tile  
- Agents: **rabbits** stored as `[x, y, energy]`  
- Each tick: **propose moves → resolve conflicts → move → eat → regrow → reproduce → cull**  
- UI modes: **headless** (prints stats) or **curses** (interactive)  
- Deterministic when `--seed` is set

**Repo layout**
```
EcoSim.py   # simulation loop and game logic
tui.py      # curses renderer (grid + HUD + energy panel)
config.py   # CLI flags & validation
```

---

## 🎮 Controls (curses UI)

- `p` — pause / resume  
- `q` — quit  

Legend:
- `"` = grass  
- `.` = dirt (regrowing)  
- `r` = rabbit on dirt  
- `R` = rabbit on grass

Top status shows: `tick | rabbits | grass | fps`.  
Right panel shows population, mean/min/max energy, and an energy histogram.

---

## ⚙️ Install & Run

**Python 3.10+ recommended**

**Windows (enable curses):**
```bash
pip install windows-curses
```

**Run headless:**
```bash
python EcoSim.py --ui none --width 30 --height 15 --ticks 200 --seed 42
```

**Run with curses UI:**
```bash
python EcoSim.py --ui curses --width 30 --height 15 --tps 8 --fps 60 --seed 7
```

Try a small board:
```bash
python EcoSim.py --ui curses --width 20 --height 10 --rabbits 15 --capacity 1 --regrow 10
```

---

## 🛠️ CLI Options

| Flag | Default | Description |
|---|---:|---|
| `--width` | `30` | Grid width |
| `--height` | `15` | Grid height |
| `--ticks` | `200` | Total ticks to simulate |
| `--capacity` | `1` | **Max rabbits allowed on a tile** |
| `--render-every` | `1` | Print one status line every K ticks (headless) |
| `--rabbits` | `20` | Initial rabbit count |
| `--regrow` | `10` | Grass regrowth delay (ticks) |
| `--seed` | `None` | RNG seed (set for reproducible runs) |
| `--ui` | `none` | `none` or `curses` |
| `--fps` | `60.0` | Frames/sec for curses rendering |
| `--tps` | `8.0` | Simulation ticks/sec |
| `--energy-start` | `5` | Starting energy per rabbit |
| `--move-cost` | `2` | Energy cost when moving (N/E/S/W) |
| `--idle-cost` | `0` | Energy cost when staying idle |
| `--eat-gain` | `4` | Energy gained when eating grass |
| `--repro-threshold` | `10` | Minimum energy needed to reproduce |
| `--repro-cost` | `5` | Energy deducted from parent at birth |
| `--infant-energy` | `None` | Newborn energy (defaults to `repro_cost` if not set) |

> 💡 **Balance tip:** Using a small `--idle-cost` (e.g., `1`) and a higher `--move-cost` (e.g., `2`) prevents “idle farming” when the grid is packed.
> 💡 **Note:** All default values for flags in `config.py` may not match the above list

---

## 🧠 How It Works

### Grid & Rabbits
- **Grid cell** = `[grass_timer, free_slots]`  
  - `grass_timer == 0` → grass present  
  - `free_slots` = how many more rabbits the tile can hold (capacity minus occupancy)
- **Rabbit** = `[x, y, energy]`

### Per-Tick Order
1. **Decide moves** — each rabbit proposes a target (or stays if OOB).  
2. **Resolve conflicts** — **custom lottery algorithm**:  
   - Count **existing occupants** on each target tile (`same_rabbit_pos`).  
   - Compare **number of proposals** to **remaining capacity**.  
   - If oversubscribed, choose winners uniformly at random using the shared RNG; losers stay put.  
3. **Apply moves** — update positions, adjust per-tile `free_slots`, charge `move-cost`/`idle-cost`.  
4. **Eat** — if `grass_timer == 0`, the rabbit gains `eat-gain`, and the cell timer is set to `--regrow`.  
5. **Regrow** — decrement timers by 1 on all tiles (skip tiles eaten this tick).  
6. **Reproduce** — if energy ≥ threshold: pay `repro-cost` and spawn in an adjacent tile **only if it has free capacity** (parent tile as fallback). Spawning consumes a `free_slot`.  
7. **Cull** — rabbits with `energy ≤ 0` are removed and their tile frees a `free_slot`.

---

## 🔍 Design Notes

- **Conflict resolution is deterministic** when `--seed` is set (shared RNG).  
- **Capacity is enforced strictly** via `free_slots` bookkeeping on move, birth, and death.  
- **Simple heuristics** (random movement) keep the core loop easy to read and extend.

---

## 🧭 Roadmap

- Reproduction cooldown
- Global metabolic tax per tick (base energy drain)  
- Local sensing: prefer nearby grass over random moves  
- Seasons: time-varying `--regrow` for cycles  
- Predators with simple chase rules

---

## 👨‍💻 Author
### Pratham Shah
📫 [LinkedIn](https://www.linkedin.com/in/pratham-shah-057274190/) | 🌐 [GitHub](https://github.com/prathamshah2207)
MIT — do whatever, be kind, give credit.
