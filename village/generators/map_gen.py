import random as r
import numpy as np
from scipy.ndimage.interpolation import zoom
import random as r
import json

'''
# read file
with open('example.json', 'r') as myfile:
    data=myfile.read()

# parse file
obj = json.loads(data)

# show values
print("usd: " + str(obj['usd']))
print("eur: " + str(obj['eur']))
print("gbp: " + str(obj['gbp']))
'''

class MapGen:

    def __init__(self, seed=None):
        self.land = '.'
        self.water = ' '
        self.base = 'B'

        # Seed block
        self.seed = seed
        if self.seed == None:
            self.seed = r.randint(1,999999)

        r.seed(self.seed)
        np.random.seed(self.seed)

        np.set_printoptions(threshold=10000)
        arr = np.random.uniform(size=(6, 12))
        arr = zoom(arr, 12)
        arr = arr > 0.75
        arr = np.where(arr, self.water, self.land)
        self.arr = arr

        self._populate_landscape('t', 1, 40) # tree
        #self._populate_landscape('f', 1, 10) # flower
        self._populate_landscape('o', 1, 60) # rock
        self._populate_landscape('*', 1, 60) # bush
        self.define_base()

    def _populate_landscape(self, to_add, min, max):
        h = self.arr.shape[0]
        w = self.arr.shape[1]
        for i in range(h):
            for j in range(w):
            	if (r.randint(min, max) == 1) and (self.arr[i,j] == self.land):
                	self.arr[i,j] = to_add

    def define_base(self):
        '''
        Search for a 5x5 space on the map to call home
        '''
        found = False
        padding = 7
        base_size = 3

        while not found:

            guess = (r.randint(padding, self.arr.shape[0] - padding),
                    r.randint(padding, self.arr.shape[0] - padding))

            found = True

            for i in range(guess[0], guess[0] + base_size):
                for j in range(guess[1], guess[1] + base_size):
                    if self.arr[i,j] == self.water:
                      found = False

        #print(f'set base cornerstone at {guess}')
        for i in range(guess[0], guess[0] + base_size):
            for j in range(guess[1], guess[1] + base_size):
                self.arr[i,j] = self.base
 
    def out(self):
        print(f"The world is {self.arr.shape}")
        for l in self.arr:
            print(''.join(l))

    def export(self):
        # translate into objects for the MapParser
        m = ''
        for l in self.arr:
          m += ''.join(l)
          m += '\n'
        return m
         
    def get_map(self):
        return self.arr()

