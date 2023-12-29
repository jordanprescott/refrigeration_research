from SystemEvents import *
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from typing import List

class AnimChannel():
    def __init__(self, channel):
        self.channel = channel

    def update(self, ax):
        raise NotImplementedError

class Animator():
    def __init__(self, animChannels: List(AnimChannel), sim):
        self.animChannels = animChannels
        self.sim = sim
        fig, ax = plt.subplots()
        self.fig = fig
        self.ax = ax


    def animate(self, _):
        self.sim.step()

        self.ax.clear()
        
        for aCh in self.animChannels:
            aCh.update(self.ax)

    def runAnimation(self, interval, frames, fileName=None, fps=10):
        ani = FuncAnimation(self.fig, self.animate, interval=interval, frames=frames)
        
        if fileName:
            ani.save('animation.gif', writer='imagemagick', fps=fps)
        plt.show()


#--------------------

class Compressor(AnimChannel):
    def __init__(self, channel, pos, size):
        super().__init__(self, channel)
        self.pos = pos
        self.size = size

    def update(self, ax):
        sv = self.channel.value

        ax.add_patch()

