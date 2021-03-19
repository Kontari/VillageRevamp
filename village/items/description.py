from village.generators import *

import random


class Description:

    def __init__(self):
        self.name = gen_name()
        self.height = str(randint(3,6))
        self.weight = str(randint(100,200))




d = Description()
