from village.items.skills import *
from village.items.description import *
from village.routines.routine import *

class Item(object):
    '''
    Parent item object.

    Examples: pickaxe, cool hat, shoes

    Described as a type 0 object within the engine
    '''
    def __init__(self, oid, uid, dx=0, dy=0, name='', path=True):
        self.pathable = path
        self.name = name
        self.oid = oid
        self.uid = uid
        self.dx = dx
        self.dy = dy
        self.current_task='idle'
        self.sprite = '?'
        # Used for finding objects obtainable
        self.locked = False
        self.held_by = None

    def set_loc(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def get_loc(self):
        return self.dx, self.dy

    def tick(self):
        # TODO: ensure this is a good idea
        pass

class NPC(Item):
    '''
    NPC items have routines, inventories and skills

    Examples: dwarf, deer, goblin
    Described as a type 1 object within the engine
    '''
    def __init__(self, sid, uid, x, y, sprite='?', name='', path=False):
        super().__init__(sid, uid, x, y, name=name, path=path)
        self.description = Description()
        self.skills = Skills()

        self.name = self.description.name
        self.sprite = sprite
        # self.current_task

        self.current_routine = None
        self.routines = []
        self.action_que = []
        self.inventory = []

    def tick(self):
        pass

class Active(Item):
    '''
    npcs without skills

    Examples: interactables, chests, doors
    Described as a type 2 object within the engine
    '''
    def __init__(self, sid, uid, x, y, sprite='?', name='', path=False):
        super().__init__(sid, uid, x, y, name=name, path=path)
        self.sprite = sprite
        self.current_routine = None
        self.routines = []
        self.action_que = []
        self.inventory = []

    def tick(self):
        pass

class ItemManager:
    '''
    Creates items and stores metadata
    '''
    def __init__(self, sim_log, map_inst, engine_defs):
        self.sim_log = sim_log
        self.map_inst = map_inst
        self.engine_defs = engine_defs
        self.engine = None
        self.rman = None
        self.unique_id_counter = 1000

        self.str_to_oid = {}
        for oid, args in self.engine_defs.items():
            self.str_to_oid[args['name']] = oid

        # Stores items by ids
        self.by_unique = {}
        self.by_static = {}

        # Holds every item in order of initial creation
        self.all = []
        # Stores uids of all items with routines
        self.with_routines = []
        # Stores uids of all npcs
        self.npcs = []

    def _factory_init(self, engine, rman):
        self.engine = engine
        self.rman = rman

    def _increment_static_id_counter(self):
        self.unique_id_counter += 1

    def init_world_chest(self, list_of_commands):

        if not self.map_inst.cornerstone_chest:
            self.sim_log.log(f'cornerstone chest not foudn to spawn items in!')
            return

        x, y = self.map_inst.cornerstone_chest
          
        for n, oid in list_of_commands:
            for _ in range(n):
                self.add_item(oid, x, y, spawn_onto_tile=False)

    def uid_is_oid(self, item_uid, item_oid):
        '''
        Checks if passed uid is an instance of oid
        '''
        if item_oid in self.by_static:
            if item_uid in self.by_static[item_oid]:
                return True
        return False

    def lookup(self, uid):
        if uid in self.by_unique:
            return self.by_unique[uid]
        else:
            raise TypeError

    def lookup_oid(self, oid):
        if oid in self.by_static:
            return self.by_static[oid]
        else:
            raise TypeError

    def lookup_str_to_oid(self, item_name):
        '''
        Matches a string to it's oid value.
        '''
        if item_name in self.str_to_oid:
            return self.str_to_oid[item_name]
        self.sim_log.warn(f'item.py could not find item_name: {item_name}') 

    def lookup_uid_held_status(self, uid):
        '''
        See if a uid is being held or in use

        Returns:
        0 : the item is on the ground
        #1 : the item is being held by an npc
        #2 : the item is being held by an active
        #3 : the item is in a chest
        or uid of item
        '''
        item = self.lookup(uid)
        x, y = item.get_loc()
        tile = self.map_inst.get_tile(x, y)

        self.sim_log.debug(f'finding... {item.name}@{item.get_loc()}')

        # TODO: add check that the item is actually
        # not an npc or active

        if item.uid in tile.items:
            # The item is on the ground, return specific
            # hardcode for this case
            return 0
        else:
            for iter_uid in tile.items:
                item_search = self.lookup(iter_uid)
                if hasattr(item_search, 'inventory'):
                    if item.uid in item_search.inventory:
                        # If an item is holding it, return the holding items uid
                        self.sim_log.debug(f'{item.name}@{item.get_loc()} held by {item_search.name}')
                        return item_search.uid

            self.sim_log.warn(f'bad from iman.lookup_uid_held_status {item.name}@{item.get_loc()}')
            #self.sim_log.log(f'item {item.name} exists in the aether!')
            return 0

    def get_number_of_item(self, item_name):
        oid = self.lookup_str_to_oid(item_name)
        if oid in self.by_static:
            return len(self.by_static[oid])
        return 0

    def does_item_have_oid(self, item, oid):
        '''
        2. verify uid1 is a valid npc or active object
        3. (if 1 and 2) check if uid2 in uid1.inventory
        '''
        for uid in item.inventory:
            if self.by_unique[uid].oid == oid:
                #self.sim_log.log('item has oid')
                return True
        return False

    def get_unlocked_items_by_oid(self, oid):
        unlocked = []

        if oid not in self.by_static:
            self.sim_log.debug(f'No objects with oid {oid} found')
            return []

        for item in self.by_static[oid]:
            if not self.lookup(item).locked:
                unlocked.append(item)

        return unlocked

    def transfer_ownership(self, item_to_transfer_uid, item_to_recv_uid):
        self.trans_item = self.lookup(item_to_transfer_uid)
        self.gets_item = self.lookup(item_to_recv_uid)

        self.gets_item.inventory.append(item_to_transfer_uid)
        x, y = self.gets_item.get_loc()
        self.trans_item.set_loc(x, y)

        # TODO: remove old item from old invent
        # OR only use when spawning?

    def add_item(self, static_id, x, y, spawn_onto_tile=True, place=True):
        static_id = str(static_id)
        args = self.engine_defs[static_id]
        unique_id = self.unique_id_counter

        # -- Item Type -- #
        if args['type'] == 0:
            new_item = Item(static_id, unique_id, x, y, name=args['name'])
        elif args['type'] == 1:
            new_item = NPC(static_id, unique_id, x, y, sprite=args['sprite'], name=args['name'], path=['path'])
            self.npcs.append(unique_id)
            self.sim_log.debug(f'Spawned {static_id}:{args["name"]} -- {x} {y}')
        elif args['type'] == 2:
            new_item = Active(static_id, unique_id, x, y, sprite=args['sprite'], name=args['name'], path=['path'])
            self.sim_log.debug(f'++Active({static_id}, {unique_id}...)')

        # Add to static id (oid) library
        if static_id in self.by_static:
            self.by_static[static_id].append(unique_id)
        else:
            self.by_static[static_id] = [unique_id]

        if 'routines' in args:
            # Add specified routines
            new_item.routines = self.rman.parse_list_to_routines(args['routines'])
            self.with_routines.append(unique_id)

        if 'path' in args:
            new_item.pathable = args['path']

        if place is True:

            if spawn_onto_tile == False:
                # ensure there is an invent there to spawn in
                if not self.map_inst.try_add(x, y, unique_id):
                    spawn_onto_tile = True
                    self.sim_log.debug('An object falls to the ground!')
            if spawn_onto_tile == True:
                # Place item on map tile x, y
                self.map_inst.get_tile(x, y).add_item(unique_id)
                self.sim_log.debug(f'An object spawns at {x} {y}')

        # Populate storage with new item
        self.all.append(new_item)

        self.by_unique[unique_id] = new_item
        # End with increment and logging
        self._increment_static_id_counter()

        # TODO: handle special items here
        self.sim_log.log(f'Spawned {static_id}:{unique_id}:{args["name"]} @ {x} {y}')

        #self.sim_log.log(f'--{unique_id}--end--')

        return unique_id
