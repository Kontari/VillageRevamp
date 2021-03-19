from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from village import map_gen
from math import floor, sqrt
import numpy as np
import random as r


class GameMap:
    '''
    A 2D array of Tile objects, which hold uids.
    '''
    def __init__(self, sim_log, terminal_print=True):
        self.sim_log = sim_log

        # Generate map and parse into game objects
        tmp_map = map_gen.MapGen()
        self.cornerstone = None
        self.seed = tmp_map.seed
        self.rooms = {}
        self.h, self.w = tmp_map.arr.shape
        self.world = self._map_grid_to_tiles(tmp_map.arr)

        # NOTE: an external call passing iman and engine
        # is required for many functions to work properly
        self.iman = None
        self.engine = None

        # NOTE: set when _inflate_world() is called
        self.cornerstone = None
        self.cornerstone_chest = None

    def _factory_init(self, iman, engine):
        self.iman = iman
        self.engine = engine
        self._inflate_world()
        self.get_pathing_matrix()
        self.sim_log.log(f'World has been generated from grid, size {self.h}x{self.w}')

    def _inflate_world(self):
        '''
        Parses the map looking for items that need to be spawned, then spawns them
        '''
        to_gen = {}
        for uid in self.engine.engine_defs.keys():
            # Make a list of items to construct from sprites  
            if int(uid) < 1000:
                # NOTE: any oid below 1000 should have a sprite variable
                to_gen[self.engine.engine_defs[uid]['sprite']] = uid
        # TODO: make this more elegant. This serves to remove the empty
        # ascii water to prevent it becoming tons of objects
        #del to_gen[' ']

        placed_cornerstone = False
        placed_chest = False

        for i in range(self.w):
            for j in range(self.h):
                # For ascii that should become objects, spawn objects
                if self.world[i,j].type in to_gen:
                    if not placed_cornerstone and self.world[i,j].type == 'B':
                        self.iman.add_item(64, i, j) # ID 64 = base cornerstone
                        self.cornerstone = (i, j)
                        placed_cornerstone = True
                    elif not placed_chest and self.world[i,j].type == 'B':
                        self.iman.add_item(10, i, j) # ID 10 = chest
                        self.cornerstone_chest = (i, j)
                        self.sim_log.log(f'cornerstone chest placed at {i},{j}')
                        placed_chest = True
                    else:
                        self.iman.add_item(to_gen[self.world[i,j].type], i, j)
 
    def _map_grid_to_tiles(self, old_map):
        self.w, self.h = old_map.shape
        base_map = np.tile(None, old_map.shape)
        for i in range(self.w):
            for j in range(self.h):
                base_map[i,j] = Tile(ground=old_map[i,j])
                # Select first room inst
                if old_map[i,j] == 'B' and self.cornerstone == None:
                    self.sim_log.log(f'Cornerstone placed at {i},{j}')
                    self.cornerstone = (i,j)
        return base_map

    def get_empty(self):
        return self.cornerstone

    def get_active_tile_item(self, x, y):

        # if empty tile, return tile.invent
        # (tile contains no items or only type 0 items)
        for item_uid in self.world[x,y].items:
            item = self.iman.by_unique[item_uid]
            if hasattr(item, 'inventory'):
                #self.sim_log.log(f'get_active_tile_item() -> {item.name}')
                return item
        return None     


    def get_tile(self, x, y):
        # TODO: check bounds?
        return self.world[x,y]

    def get_path(self, x1, y1, x2, y2):
        #TODO: this will incur large overhead, instead generate one
        # pathing map per tick
        self.sim_log.debug(f'get_path() --> {x1}, {y1}: {x2}, {y2}')
        matrix = self.get_pathing_matrix()
        grid = Grid(matrix=matrix)
        start = grid.node(x1, y1)
        end = grid.node(y2, x2)
        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        path, runs = finder.find_path(start, end, grid)
        self.sim_log.debug(f'{path}')
        return path

    def contained_items(self, x, y):
        pass 

    def _lookup_uid(self, uid):
        for i in range(self.w):                                       
            for j in range(self.h):                                   
                if int(uid) in self.world[i,j].items:
                    return i, j
        return None, None

    def try_add(self, x, y, uid):
        item = self.get_active_tile_item(x, y)
        if item:
            item.inventory.append(uid)
            #self.sim_log.log(f'{item.name} gets {uid}')
            return True
        self.sim_log.warn('warning: item coldnt be added to invent')
        return False

    def find_nearest(self, item, oid, return_path=True):
        '''
        Find the nearest instance of an oid near a uid, if found
        return a path to the item.

        ERRORS:
         currently we dont search active items invents
         returning nothing causes a crash
        '''
        if oid in self.iman.by_static:
            # TODO: add iman function to return available items
            viable_items = self.iman.get_unlocked_items_by_oid(oid)
        else:
            # It doesnt exist
            self.sim_log.warn(f'item with oid:{oid} not found in item manager db!')
            return 0, None

        list_o_dist = []

        x1, y1 = item.get_loc()
        dist = 999.9
        chosen_item = None
        self.sim_log.log(f'viable {oid} items: {viable_items}')

        # TODO: Make sure the item isnt being held in
        # another NPCs inventory...lol
        for item_uid in viable_items:
            m_item = self.iman.by_unique[item_uid]

            x2, y2 = m_item.get_loc()
            m_dist = self._calc_dist(x1, x2, y1, y2)

            if m_dist < dist:
                dist = m_dist
                chosen_item = m_item        

        if chosen_item:
            self.sim_log.log(f'{item.name} wants to obtain a path to {m_item.name}({m_item.uid}@{m_item.get_loc()})')

            if not hasattr(m_item, 'inventory'):
                # Lock the item so others cant pick it up
                m_item.locked = True

        else:
            self.sim_log.warn(f'{item.name} failed to obtain a path: {list_o_dist}')
            return 0, None

        # TODO: items inside chests arent counted here?

        if return_path:
            x1, y1 = item.get_loc()
            x2, y2 = m_item.get_loc()
            # NOTE: error here where x2 and y2 are flipped? needs deep look@
            self.sim_log.log(f'generating path {x1},{y1} --> {x2},{y2}')

            path_to_item = self.get_path(x1, y1, x2, y2)
            #self.sim_log.log(f'mapinst: path is {path_to_item}')

            # Remove step where uid would move onto tile containing item
            if len(path_to_item) > 1:
                path_to_item.pop()

            #self.sim_log.log(f'mapinst: path is {path_to_item}')
            return m_item.uid, path_to_item


    def _calc_dist(self, x1, x2, y1, y2):
        dist = sqrt( ((x1-x2)**2)+((y1-y2)**2) ) 
        return dist    

    def _add_room(self, top_l, bot_r, name):
        self.home = Room(name, top_l, bot_r, size)

    def get_str(self, row_num, mode=1):
        tmp = ''

        if (row_num < 0) or (row_num > len(self.world) - 1):
            return tmp

        for i in self.world[row_num]:
            if mode == 1:
                # chk 4 itm
                spr = i.type
                if i.items:
                    spr = self.iman.by_unique[i.items[-1]].sprite
                tmp += spr
            elif mode == 2:
                if len(i.items) == 0:
                    spr = '-'
                else:
                    # TODO: improve this flow with new pathing utility functions
                    spr = ('#','-')[self.iman.by_unique[i.items[0]].pathable]
                tmp += spr
            elif mode == 3:
                tmp += str(int(floor(i.heat)))
            elif mode == 4: # TODO
                tmp += str(int(floor(i.heat)))
            elif mode == 5:
                spr = ' '
                if len(i.items) != 0:
                    for i_uid in i.items:
                        item = self.iman.lookup(i_uid)
                        # TODO: improve this flow with new pathing utility functions
                        if hasattr(item, 'inventory'):
                            # DEBUG ZONE
                            if item.name not in ['tree','rock','bush']:
                                spr = item.sprite
                tmp += spr

        return tmp

    def get_pathing_matrix(self):
        '''
        get a 2d list of bools where 1s are pathable
        and 0s aren't
        '''
        path_table = []
        tmp = []

        for i in range(self.w):
            for j in range(self.h):
                tmp.append(self.check_pathable(i,j))
            path_table.append(tmp)
            tmp = []
        #self.sim_log.log(path_table)
        return path_table

    def check_pathable(self, x1, y1):
        # TODO: check bounds?
        for item_id in self.world[x1,y1].items:
            if self.iman.lookup(item_id).pathable == False:
                return 0
        return 1

    def _seek_tile(self, tile_value=None):
        '''
        returns a random empty tile or specified value
        '''
        if tile_value == None:
            # TODO: ensure not in any room
            # Get random empty space
            found = False
            while found == False:
                ri = r.randint(0,self.w)
                rj = r.randint(0,self.h)
                if self.check_pathable(ri, rj) == 1:
                    found = True
                    return ri, rj

        # TODO: seek item code
        pass 

class Room:
    '''
    A rectangle that will be defined as a room
    '''
    def __init__(self, name, top_l, bot_r):
        self.name = name
        self.contained = []

        for i in range(top_l[0], bot_r[0]):
            for j in range(top_l[1], bot_r[1]):
                self.contained += (i,j)

    def is_in(self, coords):
        if coords in self.contained:
            return True
        return False


class Tile:
    '''
    A 2D array of Tile objects
    '''
    def __init__(self, ground='?'):
        self.type = ground
        self.pathable = True
        self.heat = 0.0
        # Stores ints for item uid
        self.items = []

    def warm(self):
        if self.heat < 9.0:
            self.heat += 0.6

    def rem_item(self, item_id, heated=True):
        #if item_id in self.items:
        #    self.items.remove(item_id)
        self.items.remove(item_id)
        if heated: self.warm()

    def add_item(self, item_id, heated=True):
        # TODO: ensure no dups?
        self.items.append(item_id)
        if heated: self.warm()

