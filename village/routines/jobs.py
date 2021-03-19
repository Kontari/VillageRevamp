import random as r

class Job:
    '''
    '''
    def __init__(self, name):
        self.name = name


class JobManager:

    def __init__(self):
        self.jobs = []


        self.jobs['mine_rock'] = Job()

def mine_stone(level):
    '''
    Returns an item based on your level from mining stone
    '''
    return 1, 'stone'
