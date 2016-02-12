# Create a Path() class, define __hash__ and __cmp__ so that it can be used as a dictionary entry.
# Create two isValidSolution() classes, one using caching, one using on-the-fly calculation. Time to see which is faster, live cache, dead cache, or otf.

from Queue import Queue
from threading import Lock, Thread # Threads are used for the queue of PartialSolutions.
from collections import deque
from time import time
from copy import copy
from json import dumps, loads

def plus(a, b, c):
  return (a[0]+b, a[1]+c)

def format_time(seconds):
  from math import floor
  if seconds < 1:
    return '%0.2f milliseconds' % (seconds*1000)
  seconds = floor(seconds)
  time_spent = ''
  if seconds > 3600:
    time_spent += '%d hour%s' % (seconds/3600, '' if seconds/3600 == 1 else 's')
    seconds %= 60
  if seconds > 60:
    time_spent += '%d minute%s, ' % (seconds/60, '' if seconds/60 == 1 else 's')
    seconds %= 60
  if seconds > 0:
    time_spent += '%d second%s, ' % (seconds, '' if seconds == 1 else 's')
  return time_spent[:-2]

# The puzzle grid is a 7x5, so indices range from [0-6][0-4].
banned_connections = {
  (0,2):['down'],
  (0,3):['up', 'down'],
  (0,4):['up'],
  (1,0):['right'],
  (2,0):['left'],
  (4,0):['right'],
  (5,0):['left']
}

global uuidlock
uuidlock = Lock()
def getUUID():
  global uuid
  uuidlock.acquire()
  uuid += 1
  newId = uuid
  uuidlock.release()
  return newId

def findSolutions():
  global solutions
  solutions = []
  threads = []
  for i in range(16): # Number of threads
    thread = PartialSolution()
    threads.append(thread)
    thread.start()
  for thread in threads:
    thread.join()
  return solutions

class PartialSolution(Thread):
  def __init__(self, root=None):
    if root != None:
      self.color, self.blue_path, self.orange_path, self.uuid = root
      return
    super(PartialSolution, self).__init__()

  # Checks if a path is valid. Considerations are:
  # 1. Steps forward should avoid forming loops (pictured in the comments, with o as the head and .. as the potential next step)
  # 1a. Loops are OK when capturing an interesting point, such as a star or a square.
  # 1b. Loops are OK when they hit the edge of the board, as this can divide stars.
  # 2. Steps forward need to not collide with other paths
  # 3. Steps forward need to be in bounds
  # 4. Steps forward need to respect the breaks in the board
  def isValidConnection(self, dir):
    head2 = None
    if self.color == 'blue':
      head = self.blue_path[-1]
      if len(self.blue_path) > 2:
        head2 = self.blue_path[-3]
    if self.color == 'orange':
      head = self.orange_path[-1]
      if len(self.orange_path) > 2:
        head2 = self.orange_path[-3]
    if head in banned_connections and dir in banned_connections[head]:
      return False
    # 6 stars, 2 squares
    interesting_points = [(2, 0), (3, 1), (0, 2), (0, 3), (5, 2), (5, 3), (0, 1), (5, 1)]
    if dir == 'right':
      if head[0] == 6: # Issue 3
        return False
      if head[0] != 0: # Issue 1b
        # o..
        # |
        # +--
        if plus(head, 1, 1) == head2 and plus(head, 0, 0) not in interesting_points:
          return False # Issues 1 and 1a
        # +--
        # |
        # o..
        if plus(head, 1, -1) == head2 and plus(head, 0, -1) not in interesting_points:
          return False # Issues 1 and 1a
      if plus(head, 1, 0) in self.blue_path:
        return False # Issue 2
      if plus(head, 1, 0) in self.orange_path:
        return False # Issue 2
    elif dir == 'down':
      if head[1] == 4:
        return False
      if head[1] != 0:
        # +-o
        # | .
        # | .
        if plus(head, -1, 1) == head2 and plus(head, -1, 0) not in interesting_points:
          return False
        # o-+
        # . |
        # . |
        if plus(head, 1, 1) == head2 and plus(head, 0, 0) not in interesting_points:
          return False
      if plus(head, 0, 1) in self.blue_path:
        return False
      elif plus(head, 0, 1) in self.orange_path:
        return False
    elif dir == 'left':
      if head[0] == 0:
        return False
      if head[0] != 6:
        # --+
        #   |
        # ..o
        if plus(head, -1, -1) == head2 and plus(head, -1, -1) not in interesting_points:
          return False
        # ..o
        #   |
        # --+
        if plus(head, -1, 1) == head2 and plus(head, -1, 0) not in interesting_points:
          return False
      if plus(head, -1, 0) in self.blue_path:
        return False
      if plus(head, -1, 0) in self.orange_path:
        return False
    elif dir == 'up':
      if head[1] == 0:
        return False
      if head[1] != 4:
        # . |
        # . |
        # o-+
        if plus(head, 1, -1) == head2 and plus(head, 0, -1) not in interesting_points:
          return False
        # | .
        # | .
        # +-o
        if plus(head, -1, -1) == head2 and plus(head, -1, -1) not in interesting_points:
          return False
      if plus(head, 0, -1) in self.blue_path:
        return False
      if plus(head, 0, -1) in self.orange_path:
        return False
    return True

  def clone(self):
    return PartialSolution(root=(
      self.color,
      copy(self.blue_path),
      copy(self.orange_path),
      getUUID()
    ))

  def run(self):
    while True:
      from Queue import Empty
      global q
      try:
        self = q.get(True, 1)
      except Empty:
        return
      if self.color == 'blue':
        head = self.blue_path[-1]
      elif self.color == 'orange':
        head = self.orange_path[-1]
      if head in [(0, 0), (6, 0), (0, 3), (0, 4), (6, 4)]: # Valid exits
        global solutions
        if self.color == 'blue':
          solutions.append(self.blue_path)
        elif self.color == 'orange':
          solutions.append(self.orange_path)
      if self.isValidConnection('left'):
        newSolution = self.clone()
        if self.color == 'blue':
          newSolution.blue_path.append(plus(head, -1, 0))
        elif self.color == 'orange':
          newSolution.orange_path.append(plus(head, -1, 0))
        q.put(newSolution)
      if self.isValidConnection('right'):
        newSolution = self.clone()
        if self.color == 'blue':
          newSolution.blue_path.append(plus(head, 1, 0))
        elif self.color == 'orange':
          newSolution.orange_path.append(plus(head, 1, 0))
        q.put(newSolution)
      if self.isValidConnection('up'):
        newSolution = self.clone()
        if self.color == 'blue':
          newSolution.blue_path.append(plus(head, 0, -1))
        elif self.color == 'orange':
          newSolution.orange_path.append(plus(head, 0, -1))
        q.put(newSolution)
      if self.isValidConnection('down'):
        newSolution = self.clone()
        if self.color == 'blue':
          newSolution.blue_path.append(plus(head, 0, 1))
        elif self.color == 'orange':
          newSolution.orange_path.append(plus(head, 0, 1))
        q.put(newSolution)
      q.task_done()

# Check if a square is contiguous to a square in the given direction.
def isConnected(blue_path, orange_path, square, dir):
  x, y = square
  if dir == 'left':
    if x == 0:
      return False
    try:
      index = blue_path.index((x, y))
      if index > 0 and blue_path[index-1] == (x, y+1):
        return False
      if index < len(blue_path)-1 and blue_path[index+1] == (x, y+1):
        return False
    except ValueError:
      pass
    try:
      index = orange_path.index((x, y))
      if index > 0 and orange_path[index-1] == (x, y+1):
        return False
      if index < len(orange_path)-1 and orange_path[index+1] == (x, y+1):
        return False
    except ValueError:
      pass
  elif dir == 'up':
    if y == 0:
      return False
    try:
      index = blue_path.index((x, y))
      if index > 0 and blue_path[index-1] == (x+1, y):
        return False
      if index < len(blue_path)-1 and blue_path[index+1] == (x+1, y):
        return False
    except ValueError:
      pass
    try:
      index = orange_path.index((x, y))
      if index > 0 and orange_path[index-1] == (x+1, y):
        return False
      if index < len(orange_path)-1 and orange_path[index+1] == (x+1, y):
        return False
    except ValueError:
      pass
  elif dir == 'right':
    if x == 5:
      return False
    try:
      index = blue_path.index((x+1, y+1))
      if index > 0 and blue_path[index-1] == (x+1, y):
        return False
      if index < len(blue_path)-1 and blue_path[index+1] == (x+1, y):
        return False
    except ValueError:
      pass
    try:
      index = orange_path.index((x+1, y+1))
      if index > 0 and orange_path[index-1] == (x+1, y):
        return False
      if index < len(orange_path)-1 and orange_path[index+1] == (x+1, y):
        return False
    except ValueError:
      pass
  elif dir == 'down':
    if y == 3:
      return False
    try:
      index = blue_path.index((x+1, y+1))
      if index > 0 and blue_path[index-1] == (x, y+1):
        return False
      if index < len(blue_path)-1 and blue_path[index+1] == (x, y+1):
        return False
    except ValueError:
      pass
    try:
      index = orange_path.index((x+1, y+1))
      if index > 0 and orange_path[index-1] == (x, y+1):
        return False
      if index < len(orange_path)-1 and orange_path[index+1] == (x, y+1):
        return False
    except ValueError:
      pass
  return True

def isValidSolution(blue_path, orange_path):
  # This is o(n^2) and can be sped up to o(n) if the lists are sorted.
  for b in blue_path:
    for o in orange_path:
      if b == o:
        return False
  # For region definitions, we use square centers rather than square corners. The range for stars is thus [0-5, 0-3]
  stars = [(2, 0), (3, 1), (0, 2), (0, 3), (5, 2), (5, 3)]
  for i in range(3): # There are 6 stars, and each time we find one it needs to remove exactly 1 other star.
    pair_star = None
    visit_list = [stars.pop()]
    j = 0
    while j < len(visit_list):
      square = visit_list[j]
      if square in stars:
        if pair_star is not None:
          return False
        pair_star = square
      if isConnected(blue_path, orange_path, square, 'left'):
        if plus(square, -1, 0) not in visit_list:
          visit_list.append(plus(square, -1, 0))
      if isConnected(blue_path, orange_path, square, 'up'):
        if plus(square, 0, -1) not in visit_list:
          visit_list.append(plus(square, 0, -1))
      if isConnected(blue_path, orange_path, square, 'right'):
        if plus(square, 1, 0) not in visit_list:
          visit_list.append(plus(square, 1, 0))
      if isConnected(blue_path, orange_path, square, 'down'):
        if plus(square, 0, 1) not in visit_list:
          visit_list.append(plus(square, 0, 1))
      j += 1
    if pair_star is None:
      return False
    stars.remove(pair_star)
  # All stars verified, now check the colored squares

  # Black square
  visit_list = [(0, 1)]
  j = 0
  while j < len(visit_list):
    square = visit_list[j]
    # White square
    if square == (5, 1):
      return False
    if isConnected(blue_path, orange_path, square, 'left'):
      if plus(square, -1, 0) not in visit_list:
        visit_list.append(plus(square, -1, 0))
    if isConnected(blue_path, orange_path, square, 'up'):
      if plus(square, 0, -1) not in visit_list:
        visit_list.append(plus(square, 0, -1))
    if isConnected(blue_path, orange_path, square, 'right'):
      if plus(square, 1, 0) not in visit_list:
        visit_list.append(plus(square, 1, 0))
    if isConnected(blue_path, orange_path, square, 'down'):
      if plus(square, 0, 1) not in visit_list:
        visit_list.append(plus(square, 0, 1))
    j += 1
  return True

global uuid
uuid = 0
global q
q = Queue()

stages = [None]

# These are initialized separately because A. they aren't valid paths, and B. they need to have a children array defined (as a base case).
path_combos_b = {'[(3, 4)]':{'[(3, 0)]':{'parents':[], 'children':[],'cost':{'blue':None, 'blue->orange':None}}}}
path_combos_o = {'[(3, 0)]':{'[(3, 4)]':{'parents':[], 'children':[], 'cost':{'orange':None, 'orange->blue':None}}}}
# Stage 0: Calculate all blue and orange paths.
stageStart = time()
q.put(PartialSolution(root=('blue', [(3, 4)], [(3, 0)], uuid)))
blue_paths = findSolutions()
blue_paths.append([(3, 4)])
q.put(PartialSolution(root=('orange', [(3, 4)], [(3, 0)], uuid)))
orange_paths = findSolutions()
orange_paths.append([(3, 0)])
for bPath in blue_paths:
  for oPath in orange_paths:
    if isValidSolution(bPath, oPath):
      if str(bPath) not in path_combos_b:
        path_combos_b[str(bPath)] = {}
      path_combos_b[str(bPath)][str(oPath)] = {'parents':[], 'children':None, 'cost':{'blue':None, 'blue->orange':None}}
      if str(oPath) not in path_combos_o:
        path_combos_o[str(oPath)] = {}
      path_combos_o[str(oPath)][str(bPath)] = {'parents':[], 'children':None, 'cost':{'orange':None, 'orange->blue':None}}
stageEnd = time()
print 'Stage 0 done in', format_time(stageEnd-stageStart)
stageStart = stageEnd
exits_b = []
exits_o = []
to_visit = deque([([(3, 4)], [(3, 0)], 'blue')]) # Base starting point: Each path is length 1, and we start on the blue side.
while len(to_visit) > 0:
  bPath, oPath, color = to_visit.popleft()
  if color == 'blue' or oPath[-1][1] == 0: # Orange path connects to blue side or we're on the blue side, look for a new blue path.
    if str(oPath) in path_combos_o:
      for new_bPath in blue_paths:
        if new_bPath == bPath:
          continue
        if str(new_bPath) in path_combos_o[str(oPath)]: # Valid path
          path_combos_b[str(new_bPath)][str(oPath)]['parents'].append((bPath, oPath))
          path_combos_o[str(oPath)][str(new_bPath)]['parents'].append((bPath, oPath))
          path_combos_b[str(bPath)][str(oPath)]['children'].append((new_bPath, oPath))
          path_combos_o[str(oPath)][str(bPath)]['children'].append((new_bPath, oPath))
          if path_combos_o[str(oPath)][str(new_bPath)]['children'] == None:
            path_combos_b[str(new_bPath)][str(oPath)]['children'] = []
            path_combos_o[str(oPath)][str(new_bPath)]['children'] = []
            # If the node has no children, it hasn't been considered. Do so now.
            to_visit.append((new_bPath, oPath, 'blue'))
            # Remaking the blue path can only happen from the blue side.
          if new_bPath[-1] == (0, 3) and len(oPath) > 1: # Found a solution!
            path_combos_b[str(new_bPath)][str(oPath)]['cost']['blue'] = (0, 0, None)
            exits_b.append((new_bPath, oPath))
  if color == 'orange' or bPath[-1][1] == 4: # Blue path connects to orange side or we're on the orange side, look for a new orange path.
    if str(bPath) in path_combos_b:
      for new_oPath in orange_paths:
        if new_oPath == oPath:
          continue
        if str(new_oPath) in path_combos_b[str(bPath)]: # Valid path
          path_combos_b[str(bPath)][str(new_oPath)]['parents'].append((bPath, oPath))
          path_combos_o[str(new_oPath)][str(bPath)]['parents'].append((bPath, oPath))
          path_combos_b[str(bPath)][str(oPath)]['children'].append((bPath, new_oPath))
          path_combos_o[str(oPath)][str(bPath)]['children'].append((bPath, new_oPath))
          if path_combos_b[str(bPath)][str(new_oPath)]['children'] == None:
            path_combos_b[str(bPath)][str(new_oPath)]['children'] = []
            path_combos_o[str(new_oPath)][str(bPath)]['children'] = []
            # If the node has no children, it hasn't been considered. Do so now.
            to_visit.append((bPath, new_oPath, 'orange'))
            # Remaking the blue path can only happen from the blue side.
          if new_oPath[-1] == (0, 3) and len(bPath) > 1: # Found a solution!
            path_combos_o[str(new_oPath)][str(bPath)]['cost']['orange'] = (0, 0, None)
            exits_o.append((bPath, new_oPath))

stageEnd = time()
print 'Stage 1 done in', format_time(stageEnd-stageStart)
stageStart = stageEnd
# Stage 2: Calculate distance to exit at each node

def update_cost(parent, parent_cost, child, child_cost):
  if parent[0] == child[0]: # Orange path was changed to make this connection
    if parent_cost == None:
      parent_cost = (child_cost[0]+1, child_cost[1]+len(child[1]), child)
      return True
    elif parent_cost[0] > child_cost[0]:
      parent_cost = (child_cost[0]+1, child_cost[1]+len(child[1]), child)
    elif parent_cost[0] == child_cost[0] and parent_cost[1] > child_cost[1] + len(child[1]):
      parent_cost = (child_cost[0]+1, child_cost[1]+len(child[1]), child)
  else: # Blue path was changed to make this connection
    if parent_cost == None:
      parent_cost = (child_cost[0]+1, child_cost[1]+len(child[0]), child)
      return True
    elif parent_cost[0] > child_cost[0]:
      parent_cost = (child_cost[0]+1, child_cost[1]+len(child[0]), child)
    elif parent_cost[0] == child_cost[0] and parent_cost[1] > child_cost[1] + len(child[0]):
      parent_cost = (child_cost[0]+1, child_cost[1]+len(child[0]), child)
  return False

# Calculates cost at each node to reach a blue solution
to_visit = deque(exits_b)
while len(to_visit) > 0:
  bPath, oPath = to_visit.popleft()
  for parent in path_combos_b[str(bPath)][str(oPath)]['parents']:
    if update_cost(
      parent,
      path_combos_b[str(parent[0])][str(parent[1])]['cost']['blue'],
      (bPath, oPath),
      path_combos_b[str(bPath)][str(oPath)]['cost']['blue']
    ):
      to_visit.append(parent)

# Calculates cost at each node to reach an orange solution
# Calculates cost at each node to reach an orange solution, then a blue solution
to_visit = deque(exits_o)
while len(to_visit) > 0:
  bPath, oPath = to_visit.popleft()
  for parent in path_combos_o[str(oPath)][str(bPath)]['parents']:
    # I use 'any' here since 'or' is a 'short circuit' -> if the first update_cost returns true, it will neglect to run the second.
    if any([update_cost(
      parent,
      path_combos_o[str(parent[1])][str(parent[0])]['cost']['orange'],
      (bPath, oPath),
      path_combos_o[str(oPath)][str(bPath)]['cost']['orange']
    ), update_cost(
      parent,
      path_combos_o[str(parent[1])][str(parent[0])]['cost']['orange->blue'],
      (bPath, oPath),
      path_combos_o[str(oPath)][str(bPath)]['cost']['orange->blue']
    )]):
      to_visit.append(parent)

# Calculates cost at each node to reach a blue solution, then an orange solution
to_visit = deque(exits_b)
while len(to_visit) > 0:
  bPath, oPath = to_visit.popleft()
  cost = path_combos_b[str(bPath)][str(oPath)]['cost']['blue->orange']
  for parent in path_combos_b[str(bPath)][str(oPath)]['parents']:
    if update_cost(
      parent,
      path_combos_b[str(parent[0])][str(parent[1])]['cost']['blue->orange'],
      (bPath, oPath),
      path_combos_b[str(bPath)][str(oPath)]['cost']['blue->orange']
    ):
      to_visit.append(parent)

stageEnd = time()
print 'Stage 2 done in', format_time(stageEnd-stageStart)
stageStart = stageEnd

node = ([(3, 4)], [(3, 0)])
while True:
  cost = path_combos_b[str(node[0])][str(node[1])]['cost']['blue->orange']
  print node, cost[0], cost[1]
  if cost[2] is None:
    break
  node = cost[2]
while True:
  cost = path_combos_o[str(node[1])][str(node[0])]['cost']['orange']
  print node, cost[0], cost[1]
  if cost[2] is None:
    break
  node = cost[2]

print '\n\n'

node = ([(3, 4)], [(3, 0)])
while True:
  cost = path_combos_o[str(node[1])][str(node[0])]['cost']['orange->blue']
  print node, cost[0], cost[1]
  if cost[2] is None:
    break
  node = cost[2]
while True:
  cost = path_combos_b[str(node[0])][str(node[1])]['cost']['blue']
  print node, cost[0], cost[1]
  if cost[2] is None:
    break
  node = cost[2]
