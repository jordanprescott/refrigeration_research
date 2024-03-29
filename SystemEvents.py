from typing import List, Callable


class DataChannel:
    def __init__(self, name: str, value):
        self.name = name
        self.value = value
        self.subscribers: List[str] = []
        self.publishers: List[str] = []


class GroupChannel(DataChannel):
    def __init__(self, name: str, dataChannels: List[DataChannel]):
        self.dataChannels = dataChannels
        super().__init__(name, [dC.value for dC in dataChannels])
        
    
    @property
    def value(self):
        return [dC.value for dC in self.dataChannels]
    
    @value.setter
    def value(self, values):
        for i, v in enumerate(values):
            self.dataChannels[i].value = v


class Poster:
    def __init__(self, name, inputs, outputs, system):
        self.name: str = name
        self.inputs: List[DataChannel] = inputs
        self.outputs: List[DataChannel] = outputs
        self.system: Callable = system
        self.state: list = []

    def update(self):
        state = self.system(*[inp.value for inp in self.inputs])
        if len(self.outputs) == 1:
            self.state = [state]  # assume standard return format for function (return output)
        else:
            self.state = list(state)  

    def post(self):
        for output, val in zip(self.outputs, self.state):
            output.value = val

class SystemsHandler:
    def __init__(self):
        self.posters = []
        self.channels: List[DataChannel] = []

    def registerSystem(self, name: str, inputs: list[str], outputs: list[str], system: Callable):
        chDict = self.channelDict()
        inputChannels = [chDict[inp] for inp in inputs]
        outputChannels = [chDict[out] for out in outputs]
        self.posters.append(Poster(name, inputChannels, outputChannels, system))

        for ch in inputChannels:
            ch.subscribers.append(name)

        for ch in outputChannels:
            ch.publishers.append(name)

    def channelDict(self):
        return {ch.name: ch for ch in self.channels}

    def addChannel(self, channel):
        self.channels.append(channel)

    def getChannel(self, name): return [ch for ch in self.channels if ch.name == name][0]

    def globalState(self): return {ch.name: ch.value for ch in self.channels if type(ch) is DataChannel}


class BaseSimulation:
    def __init__(self, posters, channels):
        self.simulator = self.setSim(posters, channels)
        self.channelNames = list(self.simulator.globalState().keys())

    def setSim(self, systems, channels):
        sim = SystemsHandler()

        for ch in channels:
            sim.addChannel(ch)

        for sys in systems:
            sim.registerSystem(*sys)

        return sim

    def step(self):
        [P.update() for P in self.simulator.posters]
        [P.post() for P in self.simulator.posters]

class TimedSimulation(BaseSimulation):
    def __init__(self, posters, channels):
        super().__init__(posters, channels)
        self.history = [list(self.simulator.globalState().values())]

    def step(self):
        super().step()
        self.history.append(list(self.simulator.globalState().values()))

    def runSim(self, T):
        while self.simulator.globalState()['Time'] < T:
            self.step()

    def getChVal(self, channel):
        ind = self.channelNames.index(channel)
        return [timePt[ind] for timePt in self.history]

    def plotVals(self, channelList: List[List[DataChannel]]):
        import matplotlib.pyplot as plt

        N = len(channelList)
        timeVal = self.getChVal('Time')

        for i, channels in enumerate(channelList):
            plt.subplot(N, 1, i+1)
            for ch in channels:
                chVal = self.getChVal(ch)
                plt.plot(timeVal, chVal, label=ch)
            plt.legend(loc="upper left")

        plt.show()

def func2Poster(name, func):
    from inspect import signature
    return ['{}Sys'.format(name), list(signature(func).parameters), [name], func]

def fillOutChannels(channels):
    for ch in channels:
        if type(ch) is GroupChannel:
            channels += ch.dataChannels
    return channels
