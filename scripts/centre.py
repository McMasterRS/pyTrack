def parseData(data = None):
    # Returns data centred on the mean datapoint
    av = [0,0,0]
    
    for i in range(1, len(data)):
        av[0] += data[i][0]
        av[1] += data[i][1]
        av[2] += data[i][2]
        
    for i in range(1, len(data)):
        data[i] = (data[i][0] - av[0], data[i][1] - av[1], data[i][2] - av[2])
    data[0] = (0,0,0)
    return data