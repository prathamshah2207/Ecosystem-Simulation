# tui.py
import curses
from time import perf_counter

GRID_Y0 = 1
GRID_X0 = 2

# right-side panel config
PANEL_MIN_WIDTH = 24  # approx columns needed for the panel
SPARK_BARS = "▁▂▃▅▇"  # fallback: ".:-=*#" if your terminal hates unicode


def run_curses_loop(cfg, step_fn, init_state) -> None:
    """
    Setup curses and run the main loop.
    - cfg: parsed args (width, height, fps, render_every, etc.)
    - step_fn(): advances the sim by 1 tick and returns (tick, grid, rabbits)
    - init_state: optional (grid, rabbits) to draw tick 0 immediately
    """
    curses.wrapper(_main, cfg, step_fn, init_state)


def _main(stdscr, cfg, step_fn, init_state):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    tick_dt = 1.0 / cfg.tps  # simulation cadence
    frame_dt = 1.0 / cfg.fps  # render cadence

    now = perf_counter()
    next_tick = now  # first tick "now"
    next_frame = now + frame_dt
    prev_frame = now

    paused = False
    tick = 0
    grid = None
    rabbits = None

    # draw tick 0 if provided
    if init_state is not None:
        grid, rabbits = init_state
        draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est=cfg.fps, paused=paused)

    last_drawn_tick = -1
    running = True

    while running:
        now = perf_counter()

        # input
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        if key in (ord('p'), ord('P')):
            paused = not paused
            if paused:
                next_frame = now + frame_dt
            else:
                next_tick = now + tick_dt
                next_frame = now + frame_dt

        # ticks (catch up), only when not paused
        if not paused:
            max_catchup = int(cfg.tps * 2)  # cap bursts to ~2s worth
            caught = 0
            while now >= next_tick and tick < cfg.ticks and caught < max_catchup:
                tick, grid, rabbits = step_fn()
                next_tick += tick_dt
                caught += 1
                if tick >= cfg.ticks:
                    running = False
                    break

        # frame schedule (independent of ticks)
        should_draw = (now >= next_frame) and (
                paused or (tick % cfg.render_every == 0 and last_drawn_tick != tick)
        )
        if should_draw:
            dt = max(now - prev_frame, 1e-6)
            fps_est = 1.0 / dt
            draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est, paused)
            if not paused:
                last_drawn_tick = tick
            prev_frame = now
            next_frame += frame_dt

        # gentle sleep until next event
        wait_until = min(next_tick if not paused else next_frame, next_frame)
        delay_ms = max(0, int((wait_until - now) * 1000))
        curses.napms(min(delay_ms, 10))

    # final frame
    draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est=cfg.fps, paused=paused)


def draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est, paused):
    """
    Draw one full frame: status, grid, legend, and the right-side energy panel (if room).
    """
    # guard: ensure terminal is tall/wide enough for the GRID itself
    max_y, max_x = stdscr.getmaxyx()
    needed_y = GRID_Y0 + cfg.height + 2
    needed_x = GRID_X0 + cfg.width + 1
    stdscr.erase()
    if max_y < needed_y or max_x < needed_x:
        stdscr.addstr(0, 0, f"Terminal too small: need {needed_x}x{needed_y}, have {max_x}x{max_y}")
        stdscr.refresh()
        return

    # status line (row 0)
    total = cfg.width * cfg.height
    # compute grass count from timers
    grass = sum(1 for y in range(cfg.height) for x in range(cfg.width) if grid[y][x] == 0)
    if paused:
        status = (
            f'EcoSim | tick: {tick:>4} | rabbits: {len(rabbits):>3} | '
            f'grass: {grass}/{total} | fps≈{fps_est:04.1f} | [PAUSED]'
        )
    else:
        status = (
            f'EcoSim | tick: {tick:>4} | rabbits: {len(rabbits):>3} | '
            f'grass: {grass}/{total} | fps≈{fps_est:04.1f}'
        )
    stdscr.addstr(0, 0, status)

    # grid (rows 1..H, cols start at GRID_X0)
    rabbit_set = {(rx, ry) for (rx, ry, _) in (rabbits or [])}
    for y in range(cfg.height):
        for x in range(cfg.width):
            timer = grid[y][x]
            has_grass = (timer == 0)
            has_rabbit = (x, y) in rabbit_set
            if has_rabbit and has_grass:
                ch = "R"
            elif has_rabbit and not has_grass:
                ch = "r"
            elif has_grass:
                ch = '"'
            else:
                ch = "."
            stdscr.addstr(GRID_Y0 + y, GRID_X0 + x, ch)

    # legend (one line under grid)
    stdscr.addstr(GRID_Y0 + cfg.height + 1, 0, 'Legend: " grass  . dirt  r rabbit(dirt)  R rabbit(grass)')

    # energy panel on the right (only if there is room)
    panel_x = GRID_X0 + cfg.width + 4
    panel_y = GRID_Y0
    if panel_x + PANEL_MIN_WIDTH <= max_x:
        _draw_energy_panel(stdscr, rabbits or [], panel_x, panel_y)

    # flip
    stdscr.refresh()


def _draw_energy_panel(stdscr, rabbits, x0, y0):
    """
    Draw a compact energy panel:
      - population
      - mean energy, min/max
      - 5-bin histogram sparkline
    """
    # gather energies
    energies = [e for (_, _, e) in rabbits]
    pop = len(energies)
    if pop == 0:
        mean = 0.0
        emin = 0
        emax = 0
        spark = "-----"
    else:
        emin = min(energies)
        emax = max(energies)
        mean = sum(energies) / pop

        # 5-bin histogram across [emin, emax]
        bins = 5
        counts = [0] * bins
        if emin == emax:
            # put everything in the middle bin when range collapses
            mid = bins // 2
            counts[mid] = pop
        else:
            span = max(1, emax - emin)  # avoid div by zero
            for e in energies:
                idx = int((e - emin) * bins / (span + 1e-9))
                if idx == bins:  # rare case when e == emax
                    idx = bins - 1
                counts[idx] += 1

        # map counts to sparkline characters
        if max(counts) == 0:
            spark = "-----"
        else:
            levels = []
            top = max(counts)
            for c in counts:
                # scale to 0..len(SPARK_BARS)-1
                lvl = int(round((len(SPARK_BARS) - 1) * (c / top)))
                levels.append(lvl)
            spark = "".join(SPARK_BARS[lvl] for lvl in levels)

    # render lines
    stdscr.addstr(y0 + 0, x0, "── Stats ───────────────")
    stdscr.addstr(y0 + 1, x0, f"pop:     {pop:>5}")
    stdscr.addstr(y0 + 2, x0, f"E μ:     {mean:>5.1f}")
    stdscr.addstr(y0 + 3, x0, f"E min:   {emin:>5}")
    stdscr.addstr(y0 + 4, x0, f"E max:   {emax:>5}")
    stdscr.addstr(y0 + 5, x0, f"E hist:  {spark}")
    stdscr.addstr(y0 + 6, x0, "────────────────────────")
