#!/bin/python3
import curses, time, sys

WIDTH = 79
HEIGHT = 23

class GameObject:
  def __init__(self, x, y, ch, scr):
    self.x = x
    self.y = y
    self.ch = ch
    self.scr = scr
    
  def move(self, dx, dy):
    self.x += dx
    self.y += dy
    
  def draw(self):
    self.scr.addch(self.y, self.x, self.ch)

  def clear(self):
    self.scr.addch(self.y, self.x, ' ')

def clear_screen(scr):
  for row in range(HEIGHT):
    for col in range(WIDTH):
      scr.addch(row, col, ' ')

def handle_command(scr, player):
  ch = scr.getch()
  if ch == ord('Q'): sys.exit(0)
  elif ch == ord('h'): player.move(-1, 0)
  elif ch == ord('j'): player.move(0, 1)
  elif ch == ord('k'): player.move(0, -1)
  elif ch == ord('l'): player.move(1, 0)
  
def main(scr):
  curses.noecho()
  curses.cbreak()
  scr.keypad(1)
  ROWS, COLS = scr.getmaxyx()
  if (ROWS < HEIGHT or COLS < WIDTH): raise RuntimeError('Set your terminal to at least 80x24')
  curses.use_default_colors()
  player = GameObject(WIDTH//2, HEIGHT//2, '@', scr)
  monster = GameObject(WIDTH//2-5, HEIGHT//2, 'M', scr)
  objects = [player, monster]
  while True:
    curses.curs_set(0)
    clear_screen(scr)
    for object in objects: object.draw()
    scr.move(player.y, player.x)
    curses.curs_set(1)
    scr.refresh()
    handle_command(scr, player)
    for object in objects: object.clear()

try: curses.wrapper(main)
except RuntimeError as e: print(e)
