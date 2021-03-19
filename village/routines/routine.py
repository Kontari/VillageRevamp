import random as r
import copy

class RoutineEngine:
    '''
    init_base_routine_list() --> makes a base list of available routines stored in self.rdb

    parse_list_to_routines() --> turns a list of strings from engine.json into a list of
                                 routine objects that are handed to and item

    give_item_new_routine() --> takes an item and parses through its routines to assign it a
                                new one (Note: this function might be better suited within engine.py)
    '''
    def __init__(self, sim_log, game_map, engine_defs, iman):
        self.sim_log = sim_log
        self.game_map = game_map
        self.engine_defs = engine_defs
        self.iman = iman
        self.rdb = {}
        self.init_base_routine_list()

    def init_base_routine_list(self):
        '''
        Hardcoded list of routines available in the simulation
        '''
        self.rdb['idle'] = Routine('idle', ['goto base_floor'], growth=0.05)
        self.rdb['wander'] = Routine('wander', ['goto base_floor'], growth=0.01)
        self.rdb['goblin_eat'] = Routine('goblin_eat', 
                            ['seek food', 'eat food'],
                                          growth=0.02,
                                          start=0.001,
                    desc='food is needed for survival')
        self.rdb['mine_stone'] = Routine('mine_stone',['get pickaxe','goto rock', 'work rock', 'deposit all rock'], rtype=2, desc='collect stone to build things')
        self.rdb['chop_wood'] = Routine('chop_wood', ['get axe','goto tree','work tree','deposit all log'], rtype=2, desc='collect wood to build things')
        self.rdb['panic'] = Routine('panic', ['goto tree','goto rock','goto chest'], rtype=2)


        for routine, data in self.rdb.items():
            self.sim_log.log(f'{routine} --> {data}')

    def parse_list_to_routines(self, r_list):
        '''
        Takes a list of strings and translates them into
        rdb routine objects
        '''
        obj_list = []
        for r in r_list:
            if r in self.rdb:
                obj_list.append(copy.deepcopy(self.rdb[r]))
            else:
                self.sim_log.log(f'Undefined routine: {r}')
        return obj_list

    def give_item_new_routine(self, item):
        '''
        item: item to get new routine
        '''
        if not item.routines:
            self.sim_log.log('ERROR: item has no routines to choose from')
            return

        highest_desire = 0.0
        selected_routine = item.routines[0]

        for r in item.routines:
            # Find highest r.fac
            if r.fac >= highest_desire:
                selected_routine = r
                highest_desire = r.fac
            # Set all actives to false (just in case)
            r.active = False

        # Set active, reset desire
        item.current_routine = r
        selected_routine.active = True
        selected_routine.step_index = 0
        selected_routine.fac = selected_routine.starting_fac
        self.sim_log.log(f'{item.name} decides they will now {selected_routine.name}')


class Routine:

    def __init__(self, name, steps, rtype=1, desc='', growth=0.05, start=1.0):
        self.rtype=rtype
        self.name = name
        self.description = desc
        self.steps = steps
        self.growth_fac = growth 
        self.starting_fac = self.fac = start
        self.active = False
        self.step_index = 0

    def get_step(self):
        return self.steps[self.step_index]

    def next_step(self):
        self.step_index += 1
        if (self.step_index) >= len(self.steps):
            # Routine is completed
            self.reset()
            # Return token to show that routine has ended
            #return 'end'
        else:
            return self.get_step()

    def reset(self):
        self.active = False
        self.step_index = 0
        self.fac = self.starting_fac

    def tick(self):
        '''
        Routines grow in desire over time unless active
        '''
        if self.active == False:
            self.fac += self.growth_fac
            if self.fac > 10.0: self.fac = 10.0

