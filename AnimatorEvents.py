from SystemEvents import *
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from typing import List
import matplotlib.patches as mpatches
import numpy as np
from matplotlib import cm


class AnimChannel():
    def __init__(self, channel, pos, size):
        self.channel = channel
        self.pos = pos
        self.size = size
        if pos and size:
            self.coords = np.array([
                [pos[0], pos[1]],
                [pos[0] + size[0], pos[1]],
                [pos[0] + size[0], pos[1] + size[1]],
                [pos[0], pos[1] + size[1]],
            ])

    def update(self, ax):
        raise NotImplementedError





class Animator():
    def __init__(self, animChannels: List[AnimChannel], sim, xBounds, yBounds):
        self.animChannels = animChannels
        self.sim = sim
        fig, ax = plt.subplots()
        self.fig = fig
        self.ax = ax
        self.xBounds = xBounds
        self.yBounds = yBounds

    def animate(self, _):

        self.sim.step()

        self.ax.clear()

        for aCh in self.animChannels:
            self.ax.set_xlim(self.xBounds)
            self.ax.set_ylim(self.yBounds)
            aCh.update(self.ax)


    def runAnimation(self, interval, frames, fileName=None, fps=10):
        ani = FuncAnimation(self.fig, self.animate, interval=interval, frames=frames)

        if fileName:
            ani.save('animation.gif', writer='imagemagick', fps=fps)
        plt.show()


# --------------------


# compressor stuff
class Compressor(AnimChannel):
    # pos will be coordinate of bottom left corner as tuple (x, y), size will be (width, length)
    def __init__(self, channel, pos, size, numCompressors):
        super().__init__(channel, pos, size)
        self.numCompressors = numCompressors
        self.cAdded = 0

    def update(self, ax):
        ax.add_patch(mpatches.Polygon(self.coords, fill=False))
        ax.text(self.pos[0] + self.size[0], self.pos[1], '- - - 0%', fontsize=10, va='center', ha='left')
        ax.text(self.pos[0] + self.size[0], self.pos[1] + self.size[1], '- - - 100%', fontsize=10, va='center', ha='left')
        ax.text(self.pos[0] + self.size[0], self.pos[1] + self.size[1] * 0.5, ' (Percent on)', fontsize=10, va='center', ha='left')

        yBuffer = self.size[1] * 0.2

        for i in range(self.numCompressors):
            ax.text(self.pos[0] + self.size[0]/self.numCompressors * 0.5 + self.size[0] * i / self.numCompressors, self.pos[1] - yBuffer, 'C'+str(i+1), fontsize=10, va='center', ha='center')
        ax.text(self.pos[0] + self.size[0] * 0.5, self.pos[1] - 2.5 * yBuffer, 'Compressors', fontsize=10, va='center', ha='center')


class Compressors(AnimChannel):
    def __init__(self, channel, body):
        super().__init__(channel, None, None)

        xBuffer = body.size[0] * .05
        yBuffer = body.size[1] * .05

        effWidth = (body.size[0] - xBuffer) / body.numCompressors

        self.body = body

        self.coords = np.array([
            [body.pos[0] + xBuffer + effWidth * body.cAdded, body.pos[1] + yBuffer],
            [body.pos[0] + effWidth * (body.cAdded+1), body.pos[1] + yBuffer],
            [body.pos[0] + effWidth * (body.cAdded+1), body.pos[1] + body.size[1] - yBuffer],
            [body.pos[0] + xBuffer + effWidth * body.cAdded, body.pos[1] + body.size[1] - yBuffer]
        ])

        self.slideCoords = np.array([
            [body.pos[0] + xBuffer + effWidth * body.cAdded, body.pos[1] + yBuffer],
            [body.pos[0] + effWidth * (body.cAdded + 1), body.pos[1] + yBuffer],
            [body.pos[0] + effWidth * (body.cAdded + 1), body.pos[1] + self.channel.value * (body.size[1] - yBuffer)],
            [body.pos[0] + xBuffer + effWidth * body.cAdded, body.pos[1] + self.channel.value * (body.size[1] - yBuffer)]
        ])

        body.cAdded += 1

    def update(self, ax):
        if self.channel.value != -1:
            self.slideCoords[2][1] = self.body.pos[1] + self.channel.value * self.body.size[1] * 0.95
            self.slideCoords[3][1] = self.body.pos[1] + self.channel.value * self.body.size[1] * 0.95
            ax.add_patch(mpatches.Polygon(self.slideCoords, fill=True))
        ax.add_patch(mpatches.Polygon(self.coords, fill=False, color='black'))



# evaporator stuff
class Evaporator(AnimChannel):
    def __init__(self, channel, pos, size, numEvaporators):
        super().__init__(channel, pos, size)
        self.numEvaporators = numEvaporators
        self.eAdded = 0

    def update(self, ax):
        ax.add_patch(mpatches.Polygon(self.coords, fill=False))

        yBuffer = self.size[1] * 0.2

        ax.text(self.pos[0] + self.size[0] * 0.5, self.pos[1] - 2.5 * yBuffer, 'Evaporators', fontsize=10, va='center', ha='center')



class Evaporators(AnimChannel):
    def __init__(self, channel, body):
        super().__init__(channel, None, None)

        xBuffer = body.size[0] * .05
        yBuffer = body.size[1] * .07

        effWidth = (body.size[0] - xBuffer) / body.numEvaporators

        self.coords = np.array([
            [body.pos[0] + xBuffer + effWidth * body.eAdded, body.pos[1] + yBuffer],
            [body.pos[0] + effWidth * (body.eAdded + 1), body.pos[1] + yBuffer],
            [body.pos[0] + effWidth * (body.eAdded + 1), body.pos[1] + body.size[1] - yBuffer],
            [body.pos[0] + xBuffer + effWidth * body.eAdded, body.pos[1] + body.size[1] - yBuffer]
        ])

        body.eAdded += 1

    def update(self, ax):
        ax.add_patch(mpatches.Polygon(self.coords, fill=self.channel.value, edgecolor='black'))


# vessel stuff
class Vessel(AnimChannel):
    def __init__(self, channel, pos, size):
        super().__init__(channel, pos, size)

    def update(self, ax):
        ax.add_patch(mpatches.Polygon(self.coords, fill=False))
        plt.text(self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1] * .75, 'Vessel', fontsize=10, va='center', ha='center')
        plt.text(self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1] * .25, 'SP:' + str(round(self.channel.value, 5)), fontsize=10, va='center', ha='center')


# condenser stuff
class Condenser(AnimChannel):
    def __init__(self, channel, pos, size):
        super().__init__(channel, pos, size)

    def update(self, ax):
        ax.add_patch(mpatches.Polygon(self.coords, fill=False))
        plt.text(self.pos[0] + self.size[0] * 0.5, self.pos[1] + self.size[1] * 0.5, 'Condenser', fontsize=10, va='center', ha='center')


# expansion valve stuff
class ExpansionValve(AnimChannel):
    def __init__(self, channel, pos, size):
        super().__init__(channel, pos, size)
        self.coords = np.insert(self.coords, 0, [[pos[0] + size[0] * 0.5, pos[1] + size[1] * 0.5]], axis=0)
        self.coords = np.insert(self.coords, 3, [[pos[0] + size[0] * 0.5, pos[1] + size[1] * 0.5]], axis=0)



    def update(self, ax):
        ax.add_patch(mpatches.Polygon(self.coords, fill=True, color='black'))
        plt.text(self.pos[0] + self.size[0], self.pos[1] + self.size[1] * 0.5, 'Expansion Valve', fontsize=10, va='center', ha='left')


# q_out stuff
class HeatOut(AnimChannel):
    def __init__(self, channel, pos):
        super().__init__(channel, pos, None)

    def update(self, ax):
        inferno_cm = (cm.inferno(range(256)))
        scale = 0.00045  # use to normalize qin and qout, tweak internally

        ax.arrow(self.pos[0], self.pos[1], 0, self.channel.value * scale, shape='full', linewidth=3, head_width=.03,
                 color=inferno_cm[round(self.channel.value * scale * 255)])
        plt.text(self.pos[0], self.pos[1] + self.channel.value * scale * 0.5, '  Q out', fontsize=10, va='center', ha='left')


# q_in stuff
class HeatIn(AnimChannel):
    def __init__(self, channel, pos):
        super().__init__(channel, pos, None)

    def update(self, ax):
        inferno_cm = cm.inferno(range(256))
        scale = 0.00045  # use to normalize qin and qout, tweak internally

        ax.arrow(self.pos[0], self.pos[1] - self.channel.value * scale, 0, self.channel.value * scale, shape='full', linewidth=3, head_width=.03,
             color=inferno_cm[round(self.channel.value * scale * 255)], label='1')
        plt.text(self.pos[0], self.pos[1] - self.channel.value * scale * 0.5, '  Q in', fontsize=10, va='center', ha='left')


class PathArrows(AnimChannel):
    def __init__(self, vessel, compressor, condenser, expansion, evaporator):
        super().__init__(None, None, None)
        self.vessel = vessel
        self.compressor = compressor
        self.condenser = condenser
        self.expansion = expansion
        self.evaporator = evaporator

    def update(self, ax):
        ax.arrow(self.vessel.pos[0] + self.vessel.size[0], self.vessel.pos[1] + self.vessel.size[1] * 0.5,
                 (self.compressor.pos[0] - (self.vessel.pos[0] + self.vessel.size[0])), 0, shape='full',
                 linewidth=1.2,
                 head_width=0.0, color='black')
        ax.arrow(self.vessel.pos[0]+self.vessel.size[0], self.vessel.pos[1] + self.vessel.size[1] * 0.5,
                 (self.compressor.pos[0]-(self.vessel.pos[0]+self.vessel.size[0]))/2, 0, shape='full', linewidth=0.8,
                 head_width=0.03, color='black')

        ax.arrow(self.compressor.pos[0] + self.compressor.size[0] * 0.5, self.compressor.pos[1] + self.compressor.size[1],
                 0, self.condenser.pos[1] - ( self.compressor.pos[1] + self.compressor.size[1]), shape='full', linewidth=1.2,
                 head_width=0.0, color='black')
        ax.arrow(self.compressor.pos[0] + self.compressor.size[0] * 0.5,
                 self.compressor.pos[1] + self.compressor.size[1],
                 0, (self.condenser.pos[1] - (self.compressor.pos[1] + self.compressor.size[1]))/2, shape='full',
                 linewidth=0.8,
                 head_width=0.02, color='black')

        ax.arrow(self.condenser.pos[0], self.condenser.pos[1] + self.condenser.size[1] * 0.5,
                 (self.expansion.pos[0] + self.expansion.size[0] * 0.5) - self.condenser.pos[0], 0, shape='full',
                 linewidth=1.2, head_width=0.0, color='black')
        ax.arrow(self.condenser.pos[0], self.condenser.pos[1] + self.condenser.size[1] * 0.5,
                 ((self.expansion.pos[0] + self.expansion.size[0] * 0.5) - self.condenser.pos[0])/2, 0, shape='full',
                 linewidth=1.2, head_width=0.02, color='black')
        ax.arrow(self.expansion.pos[0] + self.expansion.size[0] * 0.5, self.condenser.pos[1] + self.condenser.size[1] * 0.5,
                  0, self.expansion.pos[1]+self.expansion.size[1] - (self.condenser.pos[1] + self.condenser.size[1] * 0.5),
                 shape='full', linewidth=1.2, head_width=0.02, color='black')

        ax.arrow(self.expansion.pos[0] + self.expansion.size[0] * 0.5, self.expansion.pos[1], 0,
                 self.vessel.pos[1] + self.vessel.size[1] - self.expansion.pos[1], shape='full', linewidth=1.2,
                 head_width=0.0, color='black')
        ax.arrow(self.expansion.pos[0] + self.expansion.size[0] * 0.5, self.expansion.pos[1], 0,
                 (self.vessel.pos[1] + self.vessel.size[1] - self.expansion.pos[1])/2, shape='full', linewidth=1.2,
                 head_length=0.05, head_width=0.015, color='black')

        ax.arrow(self.vessel.pos[0] + self.vessel.size[0] * 0.25, self.vessel.pos[1], 0,
                 self.evaporator.pos[1] + self.evaporator.size[1] - self.vessel.pos[1], shape='full', linewidth=1.2,
                 head_width=0.0, color='black')
        ax.arrow(self.vessel.pos[0] + self.vessel.size[0] * 0.25, self.vessel.pos[1], 0,
                 (self.evaporator.pos[1] + self.evaporator.size[1] - self.vessel.pos[1]) * 0.5, shape='full', linewidth=1.2,
                head_width=0.015, color='black')

        ax.arrow(self.vessel.pos[0] + self.vessel.size[0] * 0.75, self.vessel.pos[1], 0,
                 self.evaporator.pos[1] + self.evaporator.size[1] - self.vessel.pos[1], shape='full', linewidth=1.2,
                head_width=0.0, color='black')
        ax.arrow(self.vessel.pos[0] + self.vessel.size[0] * 0.75, self.evaporator.pos[1] + self.evaporator.size[1], 0,
                 -(self.evaporator.pos[1] + self.evaporator.size[1] - self.vessel.pos[1]) * 0.5, shape='full', linewidth=1.2,
                 head_width=0.015, color='black')
