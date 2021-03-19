import curses
from village.world.structs import GameMap

x=0
dy=0

test = GameMap()
viewmode = 1

screen = curses.initscr()
curses.curs_set(0)
curses.noecho()
screen.border('|','|','-','-','x','x','x','x')
x_len = (curses.COLS - 5)


while x != ord('q'):

    # Underlying map
    for i in range(curses.LINES - 2):
        b_str = test.get_str(dy + i, viewmode)
        screen.addstr((i + 1), 2, b_str[0:x_len])

    # Strings
    screen.addstr(curses.LINES - 3, 5, '(r)andomize world (c)enter map', curses.A_BOLD)
    screen.addstr(curses.LINES - 4, 5, '1. standard view 2. pathmap 3. heatmap', curses.A_BOLD)

    x = screen.getch()

    if x == ord('r'):
        test = GameMap()
    if x == ord('w'):
        if dy > 0:
            dy -= 1
    if x == ord('s'):
        if dy < (curses.LINES - 4):
            dy += 1
    if x == ord('c'):
            dy = 0
    if x == ord('1'):
        viewmode = 1
    if x == ord('2'):
        viewmode = 2
    if x == ord('3'):
        viewmode = 3



curses.endwin()
