from RefrigeratorSimulator import *
from AnimatorEvents import *
from SystemEvents import *

## Animation
testSim = BaseSimulation(posters, channels)
def getCh(name): return testSim.simulator.getChannel(name)

cBody = Compressor(channel=None, pos=(0.6,0.05), size=(0.25,0.5), numCompressors=4)
compressors = [Compressors(getCh(ch), cBody) for ch in ['SlideValveA', 'SlideValveB', 'SlideValveD', 'SlideValveD']]

eBody = Evaporator(channel=None, pos=(.15, -.15), size=(.3, .3), numEvaporators=5)
evaporators = [Evaporators(getCh(ch), eBody) for ch in ['EvaporatorA', 'EvaporatorB', 'EvaporatorC', 'EvaporatorD', 'EvaporatorE']]

v = Vessel(channel=getCh('SuctionPressure'), pos=(.22, .3), size=(.2, .2))

cond = Condenser(channel=None, pos=(.6, 0.7), size=(0.25, 0.1))

expn = ExpansionValve(channel=None, pos=(.3, 0.625), size=(0.03, 0.07))

qin = HeatIn(channel=getCh('TotalQin'), pos=(0.3, -0.425))

qout = HeatOut(channel=getCh('TotalQout'), pos=(0.725, 0.85))

arw = PathArrows(v, cBody, cond, expn, eBody)

a = Animator([cBody, eBody, v, cond, expn, qin, qout, arw] + compressors + evaporators, testSim, [0.1, 1], [-0.85, 1.2])
a.animate(200)
a.runAnimation(200, 20, fileName='example.gif')
