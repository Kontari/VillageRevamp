import time
import random as r

class ActionHandler:

    def __init__(self, sim_log, map_inst, engine_defs, iman, init_events=None):
        self.sim_log = sim_log
        self.map_inst = map_inst
        self.engine_defs = engine_defs
        self.iman = iman
        self.rman = None

        if init_events:
            # Inject world events on tick 0
            for event in init_events:
                self.parse_action(event)

        self.sim_log.debug('ActionHandler init')

    def _factory_init(self, rman):
        self.rman = rman

    def parse_action(self, action_token):
        # TODO: add ability to disable when running in lite mode
        tk = action_token.split(':')
        name = tk[0]
        '''
        x,y = grid coordinates
        object id = unique existing object (uid)
        item id = unique nonexistent item
        '''    
        if name == 'move':
            self._move(tk)
        elif name == 'spawn': # spawns onto a tile, where spawn_in spawns in an inventory
            self._spawn(tk)
        elif name == 'spawn_in': # spawns in an inventory on a tile
            self._spawn_in(tk)
        elif name == 'loot':
            # uid adds uid to invent. uid2 removes uid2 from invent.
            self._loot(tk)
        elif name == 'give': # Example: depositing into a chest
            # object id gives itemid to itemid
            self._give(tk)
        elif name == 'pickup':
            # Grab items from the ground
            self._pickup(tk)
        elif name == 'drop':
            # drop item to the ground
            self._pickup(tk)
        elif name == 'gen':
             #making a new item from an objectinstance
            self.sim_log.debug(f'move object {tk[1]} to {tk[2]},{tk[3]}')
        elif name == 'del':
            # removing an item
            self.sim_log.debug(f'delete object {tk[1]} on {tk[2]},{tk[3]}')

    def _move(self, tk):
        #tk: 'move', object uid, dx, dy
        uid, dx, dy = int(tk[1]), int(tk[2]), int(tk[3])
        item = self.iman.lookup(uid)

        # 0. TODO: check if tile taken
        pass


        # 1. remove obj id from current tile
        sx, sy = item.get_loc()
        tile_from = self.map_inst.get_tile(sx, sy)

        if uid not in tile_from.items:
            self.sim_log.warn(f'misalignment occured between uid:{item.name} @ {item.get_loc()} to {dx} {dy}')
            self.sim_log.warn(f'tried removing from tile at {sx} {sy} --> {tile_from.items}')

            self.sim_log.warn(f'found actual uid on {self.map_inst._lookup_uid(uid)}')
            raise uid

        tile_from.rem_item(uid)

        # 2. add id to new tile
        self.map_inst.get_tile(dx, dy).add_item(uid)

        # 3. update items coordinates
        item.set_loc(dx, dy) 

        # TODO: ensure held items by uid are also updated locally
        for invent_item_uid in item.inventory:
            tmp_item = self.iman.lookup(invent_item_uid)
            tmp_item.set_loc(dx, dy)

    def _spawn(self, tk):
        #tk: 'spawn', object id, dx, dy
        inst_id, dx, dy = int(tk[1]), int(tk[2]), int(tk[3])

        uid = self.iman.add_item(inst_id, dy, dx)

        # Place onto map
        #self.map_inst.get_tile(dx, dy).items.append(uid)

    def _spawn_in(self, tk):
        #tk: 'spawn', object id, uid
        # spawn an oid and give it to the uid
        spawned_oid, gets_uid = int(tk[1]), int(tk[2])
        new_item_uid = self.iman.add_item(spawned_oid, 0, 0, place=False)
        self.iman.transfer_ownership(new_item_uid, gets_uid)


    def _loot(self, tk):
        #tk: 'loot', uid1, uid2, uid3
        uid1, uid2, uid3 = int(tk[1]), int(tk[2]), int(tk[3])
        # uid1 adds uid2 to its inventory from uid3
        adds_item = self.iman.lookup(uid1)
        rems_item = self.iman.lookup(uid3)
        rems_item.inventory.remove(uid2)
        adds_item.inventory.append(uid2)

    def _give(self, tk):
        #tk: 'give', uid1, uid2, uid3
        uid1, uid2, uid3 = int(tk[1]), int(tk[2]), int(tk[3])
        # uid1 gives uid2 to uid3
        adds_item = self.iman.lookup(uid3)
        rems_item = self.iman.lookup(uid1)

        self.sim_log.debug(f'{rems_item.name} gives u{uid2}->{self.iman.lookup(uid2).name} to {adds_item.name}')
        rems_item.inventory.remove(uid2)
        adds_item.inventory.append(uid2)


    def _pickup(self, tk):
        '''
        tk: 'pickup', uid, uid2
        uid1 adds uid2 to it's inventory
        
        NOTE: remove before append, so the remove doesn't remove
        the latest appended item, causing an infinite loop
        This should only be used to grab items from the ground
        Loot should be used to grab items from another npc/active
        '''
        #uid, pickup_oid, x, y = tk[1], tk[2], tk[3], tk[4]
        uid = int(tk[1])
        pickup_uid = int(tk[2])

        gets_item = self.iman.by_unique[uid]
        the_item = self.iman.by_unique[pickup_uid]
         
        self.sim_log.log(f'{gets_item.name} picks up {the_item.name}')

        # loses item could be a tile, OR a uid (based on the x,y)
        #self._rem_uid_from_coords(chosen_item.uid, x, y)
        self.sim_log.log(f'grabbed @ {the_item.dx} {the_item.dy}')
        self.map_inst.get_tile(the_item.dx, the_item.dy).items.remove(pickup_uid)

        gets_item.inventory.append(the_item.uid)
        the_item.set_loc(gets_item.dx, gets_item.dy)

        self.sim_log.debug(f'{gets_item.name} picks up a {the_item.name}')

    def _select_item_matching_oid(self, oid, x, y):
        # iter through contained items
        items = self.map_inst.get_tile(x, y).items
        for item_uid in items:
            #if uid in self.iman.by_unique[item_uid].inventory:
            #    self.imnp.by_unique[item_uid].inventory.remove(uid)
            item_obj = self.iman.by_unique[item_uid]
            if int(item_obj.oid) == int(oid):
                return item_obj

    def _rem_uid_from_coords(self, uid, x, y):
        '''
        This is a challenge because a tile could just have item,
        or item holding item
        '''
        to_mod = self.map_inst.get_tile(x, y)

        # If itemless tile
        if uid in to_mod.items:
            to_mod.items.remove(uid)
        # Else iter through contained items
        for item_uid in to_mod.items:

            item = self.iman.by_unique[item_uid]
            if hasattr(item, 'inventory'):
                if uid in item.inventory:
                    item.inventory.remove(uid)


    def _inject_command(self, command):
        self.sim_log.log(f'--> {command}')
        self.parse_action(command.strip('\n'))

    def run_command(self, command):
        self.sim_log.log(f'{command}')
        self.parse_action(command.strip('\n'))

    # Routine based commands
    def parse_routine(self, item, routine, current_step, name):
        '''
        # If action que --> do it
        # Else reassign actions from current routine
        '''

        if name == 'idle':
            self.sim_log.log(f'{item.name} idles')

    def tick(self):
        '''
        1. iterate through all known objects with routines
          1a. tick all the items routine objects
          2a. inject command from action que
          2b. generate items for the next ticks action que
            3a. check if current step in routine is complete
            3b. if complete increment step
        '''
        # 1.
        for item_uid in self.iman.with_routines:
            ticking_item = self.iman.by_unique[item_uid]

            if ticking_item.current_routine == None:
                self.rman.give_item_new_routine(ticking_item)

            # 1a. tick all the items routine objects
            for routine in ticking_item.routines:
                routine.tick()

            # 2. action que decision is made here
            if ticking_item.action_que:
                # 2a. perform action specified
                self.run_command(ticking_item.action_que.pop(0))
            else:
                # 2b. generate action que items from current routine
                current_step_text = routine.get_step()
                tk = current_step_text.split(' ')
                intent = tk[0]

                if intent == 'get':
                    # TODO: wrapper function for this block
                    '''
                    # find and pathto and pickup
                    # 1. check if ticking_item has item already
                    '''
                    wanted_oid = self.iman.lookup_str_to_oid(tk[1])
                    # Check if it's being held currently
                    if self.iman.does_item_have_oid(ticking_item, wanted_oid):
                        #self.sim_log.log(f'{ticking_item.name} already has a {wanted_oid}')
                        routine.next_step()
                        #return
                        break

                    # Else get the uid of the closest matched oid
                    obtain_uid, route = self.map_inst.find_nearest(ticking_item, wanted_oid)

                    # If no items exist, return and cull routine
                    if obtain_uid == 0:
                        pass # TODO
                    elif len(route) < 2: # grab
                        # Check if the nearest one is grabbable
                        # TODO: how to check for pickup vs loot?
                        pickup_command=f'pickup:{ticking_item.uid}:{obtain_uid}'
                        from_uid = self.iman.lookup_uid_held_status(obtain_uid)

                        if from_uid == 0:
                            # Means it's on a tile so we are okay to pickup
                            pass
                        if from_uid > 0:
                            # change pickup to loot from
                            # why obtain != from?
                            pickup_command=f'loot:{ticking_item.uid}:{obtain_uid}:{from_uid}'

                        #self.sim_log.debug(f'{ticking_item.name} ++ {pickup_command}')
                        ticking_item.action_que.append(pickup_command)

                    else: # path closer, then grab
                        # TODO: add unpathability check
                        #self.sim_log.log(type(route))

                        # If you need to path to be within one space
                        if len(route) > 1:
                            self.sim_log.log(f'route: {route}')
                            for mov in route:
                                ticking_item.action_que.append(f'move:{ticking_item.uid}:{mov[0]}:{mov[1]}')

                elif intent == 'goto':
                    wanted_oid = self.iman.lookup_str_to_oid(tk[1])

                    # Else get the uid of the closest matched oid
                    obtain_uid, route = self.map_inst.find_nearest(ticking_item, wanted_oid)

                    # If no items exist, return and cull routine
                    if not obtain_uid:
                        pass
                    elif len(route) < 2: # grab
                        # Check if the nearest one is grabbable
                        # TODO: how to check for pickup vs loot?
                        #pickup_command=f'pickup:{ticking_item.uid}:{obtain_uid}'
                        #ticking_item.action_que.append(pickup_command)
                        self.sim_log.log(f'{ticking_item.name} is within range of {tk[1]}')
                        routine.next_step()
                    else: # path closer, then grab
                        # TODO: add unpathability check
                        #self.sim_log.log(type(route))

                        # If you need to path to be within one space
                        if len(route) > 1:
                            #self.sim_log.log(f'route: {route}')
                            for mov in route:
                                self.sim_log.log(f'add move {mov}')
                                ticking_item.action_que.append(f'move:{ticking_item.uid}:{mov[0]}:{mov[1]}')

                elif intent == 'work':
                    self.sim_log.debug(f'matched intent -- work {tk[1]}')
                    d_x, d_y = ticking_item.get_loc()
                    self.sim_log.debug(f'invent of {ticking_item.name}@({ticking_item.get_loc()}) {ticking_item.inventory}')

                    if len(ticking_item.inventory) > 20:
                        routine.next_step()
                    # TODO add job system
                    elif tk[1] == 'rock':
                        # stone == oid 2100
                        # NOTE: why use a spawn here if its not needed? faster to
                        # make a stone and give it to the object manually
                        spawn_rock_cmd=f'spawn_in:2100:{ticking_item.uid}'

                        for _ in range(3):
                            ticking_item.action_que.append(spawn_rock_cmd)

                elif intent == 'deposit':
                    '''
                    tk[1]: maximum amount of item to deposit
                    tk[2]: oid longname of the item to deposit
                    '''
                    self.sim_log.debug(f'matched intent -- deposit {tk[1]} {tk[2]}')

                    if tk[1] == 'all':
                        deposit_n = 100
                    else:
                        deposit_n = int(tk[1])

                    deposit_oid = self.iman.lookup_str_to_oid(tk[2])

                    d_x, d_y = ticking_item.get_loc()

                    # 1. nearest chest
                    chest_oid = '10'

                    # Else get the uid of the closest matched oid
                    chest_uid, route = self.map_inst.find_nearest(ticking_item, chest_oid)

                    if chest_uid == 0:
                        self.sim_log.log(f'{ticking_item.name}@{ticking_item.get_loc()} is stuck and screams for help!')
                        # Goblin stuck, inc stuck count and idle
                    elif len(route) < 2:
                        self.sim_log.debug(f'{ticking_item.name} is close enough to deposit')
                        deposit_count = 0

                        # perform deposit
                        for item_uid in ticking_item.inventory:

                            # check item in inv
                            #item = self.iman.lookup(item_uid)
                            #if int(item.oid) == int(deposit_oid):
                            if self.iman.uid_is_oid(item_uid, deposit_oid):
                                # trade to chest
                                deposit_command = f'give:{ticking_item.uid}:{item_uid}:{chest_uid}'
                                # uid1 gives uid2 to uid3
                                self.run_command(deposit_command)
                                deposit_count += 1
                            if deposit_count >= deposit_n:
                                break

                        self.sim_log.log(f'{ticking_item.name} deposits {deposit_count} {item_uid}')
                        routine.next_step()

                    else: # path closer
                        # TODO: add unpathability check
                        #self.sim_log.log(type(route))

                        # If you need to path to be within one space
                        if len(route) > 1:
                            for mov in route:
                                ticking_item.action_que.append(f'move:{ticking_item.uid}:{mov[0]}:{mov[1]}')


