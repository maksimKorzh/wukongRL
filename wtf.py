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
MAX_ROOM_MONSTERS = 5
MAX_ROOM_ITEMS = 2
HEAL_AMOUNT = 5
WUKONG_START_HP = 10
WUKONG_START_DEFENSE = 0
WUKONG_START_POWER = 5
HUNGRY_GHOST_HP = 5
HUNGRY_GHOST_DEFENSE = 0
HUNGRY_GHOST_POWER = 5
WHITE_BONE_DEMON_HP = 7
WHITE_BONE_DEMON_DEFENSE = 2
WHITE_BONE_DEMON_POWER = 7
BULL_DEMON_HP = 15
BULL_DEMON_DEFENSE = 5
BULL_DEMON_POWER = 10
SPIDER_QUEEN_HP = 30
SPIDER_QUEEN_DEFENSE = 7
SPIDER_QUEEN_POWER = 15
ERLAN_SHEN_HP = 50
ERLAN_SHEN_DEFENSE = 10
ERLAN_SHEN_POWER = 20

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
  def __init__(self, x, y, ch, name, scr, blocks=False, fighter=None, ai=None, item=None):
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
    self.item = item
    if self.item: self.item.owner = self
    
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
  
  def send_to_back(self, objects):
    objects.remove(self)
    objects.insert(1, self)
  
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

  def take_damage(self, damage, objects, scr):
    if damage > 0:
      self.hp -= damage
      if self.hp <= 0:
        function = self.death_function
        if function is not None: function(self.owner, objects, scr)
          
  def attack(self, target, objects, scr):
    enemy_stats = self.owner.name.capitalize() + '(HP:' + str(self.hp) + '/' + str(self.max_hp) + ' Power:' + str(self.power) + ' Defence:' + str(self.defense) + ')'
    damage = self.power - target.fighter.defense
    if damage > 0:
      if self.owner.name != 'Wukong': print_message(enemy_stats + ' attacks ' + target.name +  ' for ' + str(damage) + ' hit points.', scr)
      target.fighter.take_damage(damage, objects, scr)
    else: print_message(enemy_stats + ' attacks ' + target.name +  ' but it has no effect!', scr)

  def heal(self, amount):
    self.hp += amount
    if self.hp > self.max_hp: self.hp = self.max_hp

class BasicEnemy:
  def take_turn(self, objects, scr):
    player = objects[0]
    enemy = self.owner
    if (enemy.x, enemy.y) in visible_tiles:
      if enemy.distance_to(player) >= 2: enemy.move_towards(player.x, player.y, objects)
      elif player.fighter.hp > 0: enemy.fighter.attack(player, objects, scr)

class Item:
  def __init__(self, use_function=None):
    self.use_function = use_function
  
  def pick_up(self, objects, inventory, scr):
    if len(inventory) >= 26: print_message('Your inventory is full, cannot pick up ' + self.owner.name + '.', scr)
    else:
      inventory.append(self.owner)
      objects.remove(self.owner)
      print_message('You picked up a ' + self.owner.name + '!', scr)

  def use(self, player, objects, inventory, scr):
    if self.use_function is None: print_message('The ' + self.owner.name + ' cannot be used.')
    else:
      if self.use_function(player, objects, scr) != 'cancelled': inventory.remove(self.owner)

def cast_heal(player, objects, scr):
  if player.fighter.hp == player.fighter.max_hp:
    print_message('You are already at full health.', scr)
    return 'cancelled'
  print_message('You feel your body filling with QI!', scr)
  player.fighter.heal(HEAL_AMOUNT)

def cast_qi_attack(player, objects, scr):
  print_message('Who to attack? (enemy char, e.g. "H" or "W")', scr)
  ch = -1
  while ch == -1: ch = scr.getch()
  hit = False
  for obj in objects:
    if (obj.x, obj.y) in visible_tiles:
      if obj.fighter and obj.ch == chr(ch):
        player.fighter.attack(obj, objects, scr)
        print_message('You used QI to attack ' + obj.name.capitalize(), scr)
        hit = True
        break
  if not hit:
    print_message('There is no enemy ' + chr(ch) + '!', scr)
    return 'cancelled'

def player_death(player, objects, scr):
  global game_state
  print_message('You died!', scr)
  game_state = 'dead'
  player.ch = '%'

def enemy_death(enemy, objects, scr):
  print_message(enemy.name.capitalize() + ' is dead!', scr)
  player = objects[0]
  if player.fighter.max_hp + 5 < 99: player.fighter.max_hp += 5
  amount = 0
  if enemy.ch == 'H': amount = 1
  elif enemy.ch == 'W': amount = 3
  elif enemy.ch == 'B': amount = 5
  elif enemy.ch == 'S': amount = 7
  elif enemy.ch == 'E': amount = 9
  
  player.fighter.defense += amount
  player.fighter.power += amount
  enemy.ch = '%'
  enemy.blocks = False
  enemy.fighter = None
  enemy.ai = None
  enemy.send_to_back(objects)

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
  num_enemies = randint(0, MAX_ROOM_MONSTERS)
  for i in range(num_enemies):
    x = randint(room.x1+1, room.x2-1)
    y = randint(room.y1+1, room.y2-1)
    if not is_blocked(x, y, objects):
      choice = randint(0, 100)
      if choice < 10:
        fighter_component = Fighter(hp=ERLAN_SHEN_HP, defense=ERLAN_SHEN_DEFENSE, power=ERLAN_SHEN_POWER, death_function=enemy_death)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'E', 'erlan shen',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      elif choice < 20:
        fighter_component = Fighter(hp=SPIDER_QUEEN_HP, defense=SPIDER_QUEEN_DEFENSE, power=SPIDER_QUEEN_POWER, death_function=enemy_death)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'S', 'spider queen',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      elif choice < 40:
        fighter_component = Fighter(hp=BULL_DEMON_HP, defense=BULL_DEMON_DEFENSE, power=BULL_DEMON_POWER, death_function=enemy_death)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'B', 'bull demon',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      elif choice < 60:
        fighter_component = Fighter(hp=WHITE_BONE_DEMON_HP, defense=WHITE_BONE_DEMON_DEFENSE, power=WHITE_BONE_DEMON_POWER, death_function=enemy_death)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'W', 'white bone demon',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      else:
        fighter_component = Fighter(hp=HUNGRY_GHOST_HP, defense=HUNGRY_GHOST_DEFENSE, power=HUNGRY_GHOST_POWER, death_function=enemy_death)
        ai_component = BasicEnemy()
        enemy = GameObject(x, y,  'H', 'hungry ghost',  scr, blocks=True, fighter=fighter_component, ai=ai_component)
      objects.append(enemy)
  
  num_items = randint(0, MAX_ROOM_ITEMS)
  for i in range(num_items):
    x = randint(room.x1+1, room.x2-1)
    y = randint(room.y1+1, room.y2-1)
    if not is_blocked(x, y, objects):
      item_component = Item(use_function=cast_heal)
      item = GameObject(x, y, '!', 'QI cultivation spell', scr, item=item_component)
      objects.append(item)
      item.send_to_back(objects)

    x1 = randint(room.x1+1, room.x2-1)
    y1 = randint(room.y1+1, room.y2-1)
    if not is_blocked(x1, y1, objects) and x1 != x and y1 != y:
      item_component = Item(use_function=cast_qi_attack)
      item = GameObject(x1, y1, '~', 'QI attack spell', scr, item=item_component)
      objects.append(item)
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
  global fov_recompute, visible_tiles, all_enemies
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
  player.draw()
  scr.move(23, 0)
  scr.clrtoeol()
  scr.addstr(23,0, 'Wukong (HP:' + str(player.fighter.hp) + '/' + str(player.fighter.max_hp) + ' ' +
                   'Power:' + str(player.fighter.power) + ' ' +
                   'Defense:' + str(player.fighter.defense) + ')' + ' ' +
                   'ENEMIES:' + str(all_enemies) + ' ' +
                   '| MOVE: [hjklyubn] ITEMS: [i,.]')
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
    if obj.fighter and obj.x == x and obj.y == y:
      target = obj
      break
  if target is not None: player.fighter.attack(target, objects, scr)
  else:
    player.move(dx, dy, objects)
    fov_recompute = True
    print_message('', scr)

def handle_command(scr, objects, inventory):
  global fov_recompute
  player = objects[0]
  ch = scr.getch()
  if ch == ord('Q'): return 'exit'
  if game_state == 'playing':
    if ch == ord('h'): player_move_or_attack(-1, 0, objects, scr)
    elif ch == ord('j'): player_move_or_attack(0, 1, objects, scr)
    elif ch == ord('k'): player_move_or_attack(0, -1, objects, scr)
    elif ch == ord('l'): player_move_or_attack(1, 0, objects, scr)
    elif ch == ord('y'): player_move_or_attack(-1, -1, objects, scr)
    elif ch == ord('u'): player_move_or_attack(1, -1, objects, scr)
    elif ch == ord('b'): player_move_or_attack(-1, 1, objects, scr)
    elif ch == ord('n'): player_move_or_attack(1, 1, objects, scr)
    else:
      if ch == ord('.'):
        if len(inventory) == 0: print_message('You have no items to use!', scr)
        else:
          print_message('What to use? (inventory item, e.q. "a" or "b")', scr)
          ch = -1
          while ch == -1: ch = scr.getch()
          used = False
          for _, obj in enumerate(inventory):
            if ch - ord('a') == _:
              obj.item.use(player, objects, inventory, scr)
              used = True
          if not used: print_message('There is no such item!', scr)

      if ch == ord(','):
        for obj in objects:
          if obj.x == player.x and obj.y == player.y and obj.item:
            obj.item.pick_up(objects, inventory, scr)
            break;
      if ch == ord('i'):
        if len(inventory) == 0: print_message('Inventory is empty', scr)
        else:
          items = ''
          for _, item in enumerate(inventory): items += '(' + chr(_ + ord('a')) + ') ' + item.name + ' '
          print_message(items, scr)
      return 'didnt-take-turn'

def print_message(msg, scr):
  curses.curs_set(0)
  scr.move(22, 0)
  scr.clrtoeol()
  if len(msg) > SCREEN_WIDTH:
    scr.addstr(22,0, ' '.join(msg.split(' ')[0:10]) + '--more--')
    ch = -1
    while ch == -1: ch = scr.getch()
    print_message(' '.join(msg.split(' ')[10:]), scr)
  else: scr.addstr(22,0, msg)
  scr.refresh()
  
def main(scr):
  global fov_recompute, game_state, player_action, all_enemies
  rows, cols = scr.getmaxyx()
  if (rows < SCREEN_HEIGHT or cols < SCREEN_WIDTH):
    raise RuntimeError('Set your terminal to at least 80x24')
  scr.nodelay(1)
  curses.noecho()
  curses.raw()
  scr.keypad(1)
  curses.use_default_colors()
  fighter_component = Fighter(hp=WUKONG_START_HP, defense=WUKONG_START_DEFENSE, power=WUKONG_START_POWER, death_function=player_death)
  player = GameObject(0, 0, '@', 'Wukong', scr, blocks=True, fighter=fighter_component)
  objects = [player]
  item_component = Item(use_function=cast_qi_attack)
  item = GameObject(0,0, '!', 'QI attack spell', scr, item=item_component)
  inventory = [item, item, item]
  make_map(player, objects, scr)
  fov_recompute = True
  game_state = 'playing'
  player_action = None
  while True:
    all_enemies = 0
    for obj in objects:
      if not obj.fighter or obj.name == 'Wukong': continue
      else: all_enemies += 1
    render_all(scr, objects)
    if all_enemies == 0 or game_state == 'dead':
      if game_state != 'dead': print_message('You killed all enemies!', scr)
      ch = -1
      while ch == -1: ch = scr.getch()
      break
    player_action = handle_command(scr, objects, inventory)
    if player_action == 'exit': sys.exit(0)
    for object in objects: object.clear()
    if game_state == 'playing' and player_action != 'didnt-take-turn':
      for obj in objects:
        if obj.ai: obj.ai.take_turn(objects, scr)

try: curses.wrapper(main)
except RuntimeError as e: print(e)
