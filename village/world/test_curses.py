import curses, time, threading, sys
from village.world.structs import GameMap
from village.engine import *
from village.simulation import *

# TODO: Improve error debug from
# python3 test_curses.py 2>error.log

big = SimulationManager()
test = big.map_inst

x = dy = dx = 0
viewmode = 1

screen = curses.initscr()
curses.curs_set(0)
curses.noecho()

# Right Half Definition
RCOL = (int((curses.COLS) * 0.70) - 1)
RWIDTH = curses.COLS - RCOL
r_window = curses.newwin(curses.LINES, (RWIDTH), 0, RCOL)
r_window.border(0)

# Left Half Definition
l_window = curses.newwin(curses.LINES, (curses.COLS - RWIDTH), 0, 0)
l_window.border(0)
x_stretch_lim = (test.w - RCOL)

def redraw_log(r):
    while True:
      logged = big.sim_log.l
      # TODO: enter render loop on hook
      for event in range(curses.LINES - 2):
          if event > len(logged) - 1:
              break
          t = (logged[event]) + '      '
          if len(t) > (RWIDTH - 1):
              t = t[0:(RWIDTH - 1)]
          r.addstr(event + 1, 1, t, curses.A_BOLD)

      if len(logged) >= (curses.LINES - 2):
          action_handler.log.pop(0)

      r_window.refresh()
      time.sleep(1)


processing = threading.Thread(target=redraw_log, args=(r_window,))
processing.daemon = True
processing.start()
l_window.timeout(1000)

while x != ord('q'):

    l_window.clear()
    l_window.border(0)

    # Underlying map
    for i in range(curses.LINES - 2):
        b_str = test.get_str(dy + i, viewmode)
        if dx < 0:
            b_str = b_str[:dx]       
        if dx > 0:
            b_str = b_str[dx:]
        if len(b_str) >= (RCOL - 1):
            b_str = b_str[0:(RCOL - 1)]
        l_window.addstr((i + 1), 1, b_str[0:(RCOL - 2)])

    # Staticly placed values
    l_window.addstr(curses.LINES - 3, 2, '(r)andomize world (c)enter map', curses.A_BOLD)
    l_window.addstr(curses.LINES - 4, 2, '1. standard view 2. pathmap 3. heatmap', curses.A_BOLD)

    # Refresh
    l_window.refresh()
    x = l_window.getch()

    if x == ord('r'):
        test = GameMap()
    if x == ord('w'):
        if dy > 0: dy -= 1
    if x == ord('s'):
        if dy < (curses.LINES - 40): dy += 1
    if x == ord('a'):
        if dx > 0: dx -= 1
    if x == ord('d'):
        if dx < x_stretch_lim + 2: dx += 1
    if x == ord('c'):
            dy = dx = 0

    if x == ord('1'): viewmode = 1
    if x == ord('2'): viewmode = 2
    if x == ord('3'): viewmode = 3
    if x == ord('4'): viewmode = 4

curses.endwin()
