#!/bin/python3
import curses, time, math, sys
from random import randint

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 24
MAP_WIDTH = SCREEN_WIDTH
MAP_HEIGHT = SCREEN_HEIGHT-2
ROOM_MAX_SIZE = 12
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3

class Rect:
  def __init__(self, x, y, w, h):
    self.x1 = x
    self.y1 = y
    self.x2 = x + w
    self.y2 = y + h

  def center(self):
    center_x = (self.x1 + self.x2) // 2
    center_y = (self.y1 + self.y2) // 2
    return (center_x, center_y)
    
  def intersect(self, other):
    return (self.x1 <= other.x2 and self.x2 >= other.x1 and
            self.y1 <= other.y2 and self.y2 >= other.y1)

class Tile:
  def __init__(self, blocked, block_sight=None):
    self.blocked = blocked
    self.explored = False
    if block_sight is None:  block_sight = blocked
    self.block_sight = block_sight

class GameObject:
  def __init__(self, x, y, ch, name, scr, blocks=False, fighter=None, ai=None):
    self.x = x
    self.y = y
    self.ch = ch
    self.name = name
    self.scr = scr
    self.blocks = blocks
    self.fighter = fighter
    if self.fighter: self.fighter.owner = self
    self.ai = ai
    if self.ai: self.ai.owner = self
    
  def move(self, dx, dy, objects):
    if not is_blocked(self.x + dx, self.y + dy, objects):
      self.x += dx
      self.y += dy
  
  def move_towards(self, target_x, target_y, objects):
    dx = target_x - self.x
    dy = target_y - self.y
    distance = math.sqrt(dx ** 2 + dy ** 2)
    dx = int(round(dx / distance))
    dy = int(round(dy / distance))
    self.move(dx, dy, objects)    

  def distance_to(self, other):
    dx = other.x - self.x
    dy = other.y - self.y
    return math.sqrt(dx ** 2 + dy ** 2)
  
  def draw(self):
    if (self.x, self.y) in visible_tiles:
      self.scr.addch(self.y, self.x, self.ch)

  def clear(self):
    self.scr.addch(self.y, self.x, ' ')

class Fighter:
  def __init__(self, hp, defense, power, death_function=None):
    self.max_hp = hp
    self.hp = hp
    self.defense = defense
    self.power = power
    self.death_function = death_function

  def take_damage(self, damage):
    if damage > 0:
      self.hp -= damage
      if self.hp <= 0:
        function = self.death_function
        if function is not None: function(self.owner)
          
  def attack(self, target):
    damage = self.power - target.fighter.defense
    if damage > 0:
      print(self.owner.name.capitalize() + ' attacks ' + target.name +  ' for ' + str(damage) + ' hit points.')
      target.fighter.take_damage(damage)
    else: print(self.owner.name.capitalize() + ' attacks ' + target.name +  ' but it has no effect!')

class BasicEnemy:
  def take_turn(self, objects, scr):
    player = objects[0]
    enemy = self.owner
    if (enemy.x, enemy.y) in visible_tiles:
      if enemy.distance_to(player) >= 2: enemy.move_towards(player.x, player.y, objects)
      elif player.fighter.hp > 0: print_message('The attack of the ' + enemy.name + ' bounces off your shiny metal armor!', scr)

def create_room(room):
  global map
  for x in range(room.x1 + 1, room.x2):
    for y in range(room.y1 + 1, room.y2):
      map[x][y].blocked = False
      map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
  global map
  for x in range(min(x1, x2), max(x1, x2) + 1):
    map[x][y].blocked = False
    map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
  global map
  for y in range(min(y1, y2), max(y1, y2) + 1):
    map[x][y].blocked = False
    map[x][y].block_sight = False

def make_map(player, objects, scr):
  global map
  map = [[Tile(True) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
  rooms = []
  num_rooms = 0
  for r in range(MAX_ROOMS):
    w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
    h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
    x = randint(0, MAP_WIDTH-w-1)
    y = randint(0, MAP_HEIGHT-h-1)
    new_room = Rect(x, y, w, h)
    failed = False
    for other_room in rooms:
      if new_room.intersect(other_room):
        failed = True
        break
    if not failed:
      create_room(new_room)
      (new_x, new_y) = new_room.center()
      if num_rooms == 0:
        player.x = new_x
        player.y = new_y
      else:
        (prev_x, prev_y) = rooms[num_rooms-1].center()
        if randint(0, 1):
          create_h_tunnel(prev_x, new_x, prev_y)
          create_v_tunnel(prev_y, new_y, new_x)
        else:
          create_v_tunnel(prev_y, new_y, prev_x)
          create_h_tunnel(prev_x, new_x, new_y)
      place_objects(new_room, objects, scr)
      rooms.append(new_room)
      num_rooms += 1

def is_blocked(x, y, objects):
  if map[x][y].blocked: return True
  for obj in objects:
    if obj.blocks and obj.x == x and obj.y == y:
      return True
  return False

def place_objects(room, objects, scr):
  num_enemys = randint(0, MAX_ROOM_MONSTERS)
  for i in range(num_enemys):
    x = randint(room.x1, room.x2)
    y = randint(room.y1, room.y2)
    if not is_blocked(x, y, objects):
      #chances: 20% enemy A, 40% enemy B, 10% enemy C, 30% enemy D:
      choice = randint(0, 100)
      if choice < 20:
        fighter_component = Fighter(hp=10, defense=0, power=3)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'A', 'enemy A',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      elif choice < 20+40:
        fighter_component = Fighter(hp=5, defense=0, power=1)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'B', 'enemy B',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      elif choice < 20+40+10:
        fighter_component = Fighter(hp=16, defense=2, power=5)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'C', 'enemy C',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      else:
        fighter_component = Fighter(hp=6, defense=0, power=4)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'D', 'enemy D',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      objects.append(enemy)

def calculate_fov(player, radius=10):
  visible = set()
  for dx in range(-radius, radius+1):
    for dy in range(-radius, radius+1):
      x = player.x + dx
      y = player.y + dy
      if x < 0 or x >= MAP_WIDTH or y < 0 or y >= MAP_HEIGHT: continue
      tiles_on_line = get_line(player.x, player.y, x, y)
      blocked = False
      for tx, ty in tiles_on_line:
        if is_visible_tile(tx, ty): visible.add((tx, ty))
        else:
          visible.add((tx, ty))
          blocked = True
          break
      if blocked: continue
  return visible

def get_line(x0, y0, x1, y1):
  line = []
  dx = abs(x1 - x0)
  dy = abs(y1 - y0)
  x, y = x0, y0
  sx = 1 if x0 < x1 else -1
  sy = 1 if y0 < y1 else -1
  if dx > dy:
    err = dx // 2
    while x != x1:
      line.append((x, y))
      x += sx
      err -= dy
      if err < 0:
        y += sy
        err += dx
  else:
    err = dy // 2
    while y != y1:
      line.append((x, y))
      y += sy
      err -= dx
      if err < 0:
        x += sx
        err += dy
  line.append((x1, y1))
  return line

def is_visible_tile(x, y):
  global map
  if x >= MAP_WIDTH or x < 0: return False
  elif y >= MAP_HEIGHT or y < 0: return False
  elif map[x][y].blocked == True: return False
  elif map[x][y].block_sight == True: return False
  else: return True

def render_all(scr, objects):
  global fov_recompute
  global visible_tiles
  player = objects[0]
  if fov_recompute:
    fov_recompute = False
    visible_tiles = calculate_fov(player)
    for y in range(MAP_HEIGHT):
      for x in range(MAP_WIDTH):
        visible = (x, y) in visible_tiles
        wall = map[x][y].block_sight
        if not visible:
          if map[x][y].explored:
            if wall: scr.addch(y, x, '#')
            else: scr.addch(y, x, ' ')
        else:
          if wall: scr.addch(y, x, '#')
          else: scr.addch(y, x, '.')
          map[x][y].explored = True
  for object in objects: object.draw()
  curses.curs_set(0)
  scr.move(player.y, player.x)
  curses.curs_set(1)
  scr.refresh()

def player_move_or_attack(dx, dy, objects, scr):
  global fov_recompute
  player = objects[0]
  x = player.x + dx
  y = player.y + dy
  target = None
  for obj in objects:
    if obj.x == x and obj.y == y:
      target = obj
      break
  if target is not None:
    print_message('The ' + target.name + ' laughs at your puny efforts to attack him!', scr)
  else:
    player.move(dx, dy, objects)
    fov_recompute = True
    print_message('', scr)

def handle_command(scr, objects):
  global fov_recompute
  player = objects[0]
  ch = scr.getch()
  if ch == ord('Q'): return 'exit'
  if game_state == 'playing':
    if ch == ord('h'): player_move_or_attack(-1, 0, objects, scr)
    elif ch == ord('j'): player_move_or_attack(0, 1, objects, scr)
    elif ch == ord('k'): player_move_or_attack(0, -1, objects, scr)
    elif ch == ord('l'): player_move_or_attack(1, 0, objects, scr)
    else: return 'didnt-take-turn'

def print_message(msg, scr):
  curses.curs_set(0)
  scr.move(22, 0)
  scr.clrtoeol()
  if len(msg) > SCREEN_WIDTH:
    scr.addstr(22,0, ' '.join(msg.split(' ')[0:10]) + '--more--')
    ch = -1
    while ch == -1: ch = scr.getch()
    print_message(' '.join(msg.split(' ')[15:]), scr)
  else: scr.addstr(22,0, msg)
  scr.refresh()

def main(scr):
  global fov_recompute, game_state, player_action
  rows, cols = scr.getmaxyx()
  if (rows < SCREEN_HEIGHT or cols < SCREEN_WIDTH):
    raise RuntimeError('Set your terminal to at least 80x24')
  scr.nodelay(1)
  curses.noecho()
  curses.raw()
  scr.keypad(1)
  curses.use_default_colors()
  fighter_component = Fighter(hp=30, defense=2, power=5)
  player = GameObject(0, 0, '@', 'player', scr, blocks=True, fighter=fighter_component)
  objects = [player]
  make_map(player, objects, scr)
  fov_recompute = True
  game_state = 'playing'
  player_action = None
  while True:
    render_all(scr, objects)
    player_action = handle_command(scr, objects)
    if player_action == 'exit': sys.exit(0)
    for object in objects: object.clear()
    if game_state == 'playing' and player_action != 'didnt-take-turn':
      for obj in objects:
        if obj.ai: obj.ai.take_turn(objects, scr)

try: curses.wrapper(main)
except RuntimeError as e: print(e)
