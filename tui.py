import curses
from time import perf_counter

GRID_Y0 = 1
GRID_X0 = 2


def run_curses_loop(cfg, step_fn, init_state) -> None:
    """
    Setup curses and run the main loop.
    - cfg: your parsed args (has width, height, fps, render_every, etc.)
    - step_fn(): advances the sim by 1 tick and returns (tick, grid, rabbits)
      (you’ll define step_fn in EcoSim.py as a closure)
    - init_state: any state you want to initialize before the loop (optional)
    """

    curses.wrapper(_main, cfg, step_fn, init_state)


def _main(stdscr, cfg, step_fn, init_state):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    tick_dt = 1.0 / cfg.tps
    frame_dt = 1.0 / cfg.fps

    now = perf_counter()
    next_tick = now  # start stepping right away (after tick 0 draw)
    next_frame = now + frame_dt
    prev_frame = now
    last_drawn_tick = -1

    # Optional: show tick 0 before time starts
    if init_state is not None:
        init_grid, init_rabbits = init_state
        draw_frame(stdscr, cfg, 0, init_grid, init_rabbits, fps_est=cfg.fps)

    running = True
    tick = 0
    grid = None
    rabbits = None

    while running:
        now = perf_counter()

        # 1) Handle input (non-blocking)
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break

        # 2) Advance the simulation to "catch up" to real time
        #    (may step multiple ticks if we fell behind)
        #    Optional safety: cap the max catch-up to avoid huge bursts.
        max_catchup = int(cfg.tps * 2)  # at most 2s worth per loop; tweak if you want
        catchup = 0
        while now >= next_tick and tick < cfg.ticks and catchup < max_catchup:
            tick, grid, rabbits = step_fn()
            next_tick += tick_dt
            catchup += 1
            if tick >= cfg.ticks:
                running = False
                break

        # 3) Draw on its own schedule (independent of ticks)
        if now >= next_frame and tick % cfg.render_every == 0 and last_drawn_tick != tick:
            fps_est = 1.0 / max(now - prev_frame, 1e-6)
            draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est)
            last_drawn_tick = tick
            prev_frame = now
            next_frame += frame_dt

        # 4) Sleep briefly until the next soonest event to avoid CPU spin
        wait_until = min(next_tick, next_frame)
        delay_ms = max(0, int((wait_until - now) * 1000))
        curses.napms(min(delay_ms, 10))  # small cap keeps input responsive

    # Optional: one last draw at the final tick (if you want a final frame)
    draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est=cfg.fps)


def draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est):
    """
    Draw one full frame: status, grid, legend. Refresh ones.
    """
    # 0) guard: ensure terminal is big enough
    max_y, max_x = stdscr.getmaxyx()
    needed_y = GRID_Y0 + cfg.height + 2
    needed_x = GRID_X0 + cfg.width + 1
    stdscr.erase()
    if max_y < needed_y or max_x < needed_x:
        stdscr.addstr(0, 0, f"Terminal too small: need {needed_x}x{needed_y}, have {max_x}x{max_y}")
        stdscr.refresh()
        return

    # 1) status line (row 0)
    total = cfg.width * cfg.height
    # compute grass count here (or pass it from step_fn if you prefer)
    grass = sum(1 for y in range(cfg.height) for x in range(cfg.width) if grid[y][x] == 0)
    status = f'EcoSim | tick {tick:>4} | rabbits: {len(rabbits):>3} | grass: {grass}/{total} | fps≈{fps_est:04.1f}'
    stdscr.addstr(0, 0, status)

    # 2) grid (rows 1..H, cols start at GRID_X0)
    rabbit_set = set(rabbits)
    for y in range(cfg.height):
        for x in range(cfg.width):
            timer = grid[y][x]
            has_grass = (timer == 0)
            has_rabbit = (x, y) in rabbit_set
            # decide glyph:
            if has_rabbit and has_grass:
                ch = "R"
            elif has_rabbit and not has_grass:
                ch = "r"
            elif has_grass:
                ch = '"'
            else:
                ch = "."
            stdscr.addstr(GRID_Y0 + y, GRID_X0 + x, ch)

    # 3) legend (one line under grid)
    stdscr.addstr(GRID_Y0 + cfg.height + 1, 0, 'Legend: " grass  . dirt  r rabbit(dirt)  R rabbit(grass)')

    # 4) flip
    stdscr.refresh()
