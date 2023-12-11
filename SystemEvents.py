from typing import List, Callable


class DataChannel:
    def __init__(self, name: str, value):
        self.name = name
        self.value = value
        self.subscribers: List[str] = []
        self.publishers: List[str] = []



class Poster:
    def __init__(self, name, inputs, outputs, system):
        self.name: str = name
        self.inputs: List[DataChannel] = inputs
        self.outputs: List[DataChannel] = outputs
        self.system: Callable = system
        self.state: list = []

    def update(self):
        self.state = self.system(*[inp.value for inp in self.inputs])

    def post(self):
        for output, val in zip(self.outputs, self.state):
            output.value = val


class SystemsHandler:
    def __init__(self):
        self.posters = []
        self.channels: List[DataChannel] = []

    def registerSystem(self, name: str, inputs: list[str], outputs: list[str], system: Callable):
        inputChannels = [ch for ch in self.channels if ch.name in inputs]
        outputChannels = [ch for ch in self.channels if ch.name in outputs]
        self.posters.append(Poster(name, inputChannels, outputChannels, system))

        for ch in inputChannels:
            ch.subscribers.append(name)

        for ch in outputChannels:
            ch.publishers.append(name)

    def addChannel(self, channel):
        self.channels.append(channel)

    def globalState(self): return {ch.name: ch.value for ch in self.channels}

