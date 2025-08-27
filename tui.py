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

    tick_dt = 1.0 / cfg.tps  # simulation tick cadence
    frame_dt = 1.0 / cfg.fps  # render cadence

    now = perf_counter()
    next_tick = now  # first tick is scheduled "now"
    next_frame = now + frame_dt
    prev_frame = now

    paused = False
    tick = 0
    grid = None
    rabbits = None

    # Optional: show tick 0 immediately
    if init_state is not None:
        grid, rabbits = init_state
        draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est=cfg.fps, paused=paused)

    last_drawn_tick = -1
    running = True

    while running:
        now = perf_counter()

        # --- input ---
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        if key in (ord('p'), ord('P')):
            paused = not paused
            # realign schedulers to avoid catch-up on resume
            if paused:
                next_frame = now + frame_dt
            else:
                next_tick = now + tick_dt
                next_frame = now + frame_dt

        # --- advance sim (tick scheduler), only if not paused ---
        if not paused:
            # catch up to "now", but cap bursts to keep UI responsive
            max_catchup = int(cfg.tps * 2)  # at most ~2 seconds of ticks per loop
            caught = 0
            while now >= next_tick and tick < cfg.ticks and caught < max_catchup:
                tick, grid, rabbits = step_fn()
                next_tick += tick_dt
                caught += 1
                if tick >= cfg.ticks:
                    running = False
                    break

        # --- draw (frame scheduler), independent of ticks ---
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

        # --- gentle sleep until the next event (tick or frame) ---
        wait_until = min(next_tick if not paused else next_frame, next_frame)
        delay_ms = max(0, int((wait_until - now) * 1000))
        curses.napms(min(delay_ms, 10))

    # final frame (optional)
    draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est=cfg.fps, paused=paused)


def draw_frame(stdscr, cfg, tick, grid, rabbits, fps_est, paused):
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
    if paused:
        status = f'EcoSim | tick: {tick:>4} | rabbits: {len(rabbits):>3} | grass: {grass}/{total} | fps≈{fps_est:04.1f} | [PAUSED]'
    else:
        status = f'EcoSim | tick: {tick:>4} | rabbits: {len(rabbits):>3} | grass: {grass}/{total} | fps≈{fps_est:04.1f}'
    stdscr.addstr(0, 0, status)

    # 2) grid (rows 1..H, cols start at GRID_X0)
    rabbit_set = {(rx, ry) for (rx, ry, _) in rabbits}
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
