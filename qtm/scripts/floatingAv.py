def getObj():
    return average()


class average():
    def __init__(self):
        self.history = []
        
    def parseData(self, data = None):
        
        self.history.append(data)
        if len(self.history) > 5:
            self.history.pop(0)