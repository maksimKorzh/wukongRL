#!/bin/python3
import curses, time, sys

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 24
MAP_WIDTH = SCREEN_WIDTH
MAP_HEIGHT = SCREEN_HEIGHT-1

class Rect:
  def __init__(self, x, y, w, h):
    self.x1 = x
    self.y1 = y
    self.x2 = x + w
    self.y2 = y + h

class Tile:
  def __init__(self, blocked, block_sight=None):
    self.blocked = blocked
    if block_sight is None:  block_sight = blocked
    self.block_sight = block_sight

class GameObject:
  def __init__(self, x, y, ch, scr):
    self.x = x
    self.y = y
    self.ch = ch
    self.scr = scr
    
  def move(self, dx, dy):
    if not map[self.x + dx][self.y + dy].blocked:
      self.x += dx
      self.y += dy
    
  def draw(self):
    self.scr.addch(self.y, self.x, self.ch)

  def clear(self):
    self.scr.addch(self.y, self.x, ' ')

def create_room(room):
  global map
  for x in range(room.x1 + 1, room.x2):
    for y in range(room.y1 + 1, room.y2):
      map[x][y].blocked = False
      map[x][y].block_sight = False

def make_map():
  global map
  map = [[Tile(True) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
  room1 = Rect(10, 15, 20, 5)
  room2 = Rect(40, 15, 20, 5)
  create_room(room1)
  create_room(room2)
  
def render_all(scr, objects):
  for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
      wall = map[x][y].block_sight
      if wall: scr.addch(y, x, '#')
      else: scr.addch(y, x, '.')
  for object in objects: object.draw()
  curses.curs_set(0)
  player = objects[0]
  scr.move(player.y, player.x)
  curses.curs_set(1)
  scr.refresh()

def handle_command(scr, player):
  ch = scr.getch()
  if ch == ord('Q'): sys.exit(0)
  elif ch == ord('h'): player.move(-1, 0)
  elif ch == ord('j'): player.move(0, 1)
  elif ch == ord('k'): player.move(0, -1)
  elif ch == ord('l'): player.move(1, 0)
  
def main(scr):
  rows, cols = scr.getmaxyx()
  if (rows < SCREEN_HEIGHT or cols < SCREEN_WIDTH):
    raise RuntimeError('Set your terminal to at least 80x24')
  scr.nodelay(1)
  curses.noecho()
  curses.raw()
  scr.keypad(1)
  curses.use_default_colors()
  player = GameObject(12, 18, '@', scr)
  monster = GameObject(12, 16, 'M', scr)
  objects = [player, monster]
  make_map()
  while True:
    render_all(scr, objects)
    handle_command(scr, player)
    #for object in objects: object.clear()

try: curses.wrapper(main)
except RuntimeError as e: print(e)
