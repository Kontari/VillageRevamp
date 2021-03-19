from village.engine import *
from village.items import *
from village.world import *

from time import time
import json

class SimLog:

    def __init__(self, file_out='output.log'):
        self.l = []
        self.lim = 50
        self.c = 1
        self.tick_count = 1
        self.paused = False
        self.file_out = file_out
        self.wipe_per_tick = True #False
        self.log('Log init')
        with open(self.file_out, 'w+') as f:
            f.write('Begin log\n')

    def tick(self):
        self.tick_count += 1
        #self.log(f'--- Turn {self.tick_count} ---')


    def log(self, text, level='INFO'):

        if self.paused == True:
            return

        formatted = '[' + str(self.tick_count) + '][' + level + '] ' + str(text)
        text = formatted

        self.l.append(text)
        if self.file_out:
            self._write_to_logfile(text)

    def debug(self, text):
        self.log(text, level='DEBUG')

    def warn(self, text):
        self.log(text, level='WARN')

    def _pause_logging(self):
        self.paused = True

    def _resume_logging(self):
        self.paused = False

    def get_events(self):
        self.c += 1
        #return self.l[self.c:self.c + self.lim]
        copy = self.l
        if self.wipe_per_tick == True: self.l = []
        return copy

    def set_live(self):
        # if true, erase all items every tick
        self.wipe_per_tick = True

    def _write_to_logfile(self, text):
        with open(self.file_out, 'a') as f:
            f.write(text + '\n')

    def _generate_crash_report(self, text):
        with open(str(time()), 'a') as f:
            for line in self.l:
                f.write(line + '\n')


class SimulationManager:

    def __init__(self, game_map_object=None, item_creator=None, logging_object=None):
        self.sim_log = SimLog()

        # Load game engine definitions
        self.engine_defs = json.load(open('engine.json',))
        self.sim_log.log('Loaded game engine assets')


        self.map_inst = self.iman = self.engine = self.rman = None # this isn't needed?

        self.map_inst =     GameMap(self.sim_log, self.engine_defs)
        self.iman =     ItemManager(self.sim_log, self.map_inst, self.engine_defs)
        self.engine = ActionHandler(self.sim_log, self.map_inst, self.engine_defs, self.iman)
        self.rman   = RoutineEngine(self.sim_log, self.map_inst, self.engine_defs, self.iman) 

        '''
        Populate the ascii grid with actual objects
        This is a very verbose task and will flood the log
        '''
        self.sim_log._pause_logging()
        self.map_inst._factory_init(self.iman, self.engine)
        self.iman._factory_init(self.engine, self.rman)
        self.engine._factory_init(self.rman)
        self.sim_log._resume_logging()

        # spawn n items with oid m
        # (n, m)
        starting_items = [(10,1100), 
                          (10,1101),
                          (5,1102)]

        self.iman.init_world_chest(starting_items)

        # TODO: clarify hardcode/enable editing
        spawn_goblins = 2
        for i in range(spawn_goblins):
            self.inject_command('spawn:1:' + str(i + 10 + r.randint(10,20)) + ':' + str(r.randint(20,30)))

        '''
        # Spawn a chest
        self.inject_command('spawn:10:25:25')
        # Spawn a pickaxe on the ground
        self.inject_command('spawn_in:1100:25:25')
        # Spawn an axe on the ground
        self.inject_command('spawn_in:1101:25:25')
        '''

    def render_map(self):
        # TODO: pull mapping function up a level
        pass

    def tick(self):
        self.sim_log.tick()
        self.engine.tick()
        self.sim_log.log(f'Stone: {self.iman.get_number_of_item("stone")}', level='MANAGER')

    def inject_command(self, comm):
        self.engine._inject_command(comm)

