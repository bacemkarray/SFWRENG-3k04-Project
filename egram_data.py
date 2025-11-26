class EgramData:
    def __init__(self):
        self.time = []
        self.values = []
    
    # Method for wiping all the current egram data stored
    def clear(self):
        self.time.clear()
        self.values.clear()



egram = EgramData()

egram.time.append(40)
egram.values.append(40)
print(egram.time)
print(egram.values)
egram.clear()
print(egram.time)
print(egram.values)
