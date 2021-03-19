
class Skills:

    def __init__(self):

        # Gathering Skills
        self.woodcutting = 1
        self.fishing = 1
        self.harvesting = 1
        self.mining = 1

        # Interaction Based Skills
        self.building = 1
        self.crafting = 1


    def __str__(self):
        return '-- Skills --\nWoodcutting:' + str(self.woodcutting) + \
                                   '\nFishing:' + str(self.fishing) + \
                             '\nHarvesting:' + str(self.harvesting) + \
                                     '\nMining:' + str(self.mining) + \
                                 '\nBuilding:' + str(self.building) + \
                                 '\nCrafting:' + str(self.crafting)

