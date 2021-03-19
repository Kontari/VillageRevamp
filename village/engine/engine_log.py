

class EngineLog:

    def __init__(self, logfile='engine-run-log.log'):

        self.all_events = []
        self.verbosity = 2

    def log_event(self, in_module, text):
        print(f'[{in_module}]: {text}')

