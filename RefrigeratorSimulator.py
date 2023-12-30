from SystemEvents import *
from AnimatorEvents import *
import numpy as np
import CoolProp.CoolProp as CP

### CHANNELS

channels = [
	DataChannel('Time', 0),  # seconds
	DataChannel('DeltaT', .05),  # seconds
	DataChannel('RoomTemp', 0),  # Celsius
	DataChannel('AmbientTemp', 22),  # Celsius
	DataChannel('SuctionPressure', 18),  # psia
	DataChannel('DischargePressure', 180),  # psia
	DataChannel('TotalCompressorPower', 300),  # kW
	DataChannel('Qadded', 600),  # kW
	DataChannel('TotalQin', 600),  # kW
	DataChannel('TotalQout', 1000),  # kW
	DataChannel('TotalVolumetricHighFlow', .5),  # m^3/s
	DataChannel('TotalMassHighFlow', 1),  # kg/s
	DataChannel('TotalMassLowFlow', 1),  # kg/s
	DataChannel('SlideValveA', -1),  # -1 signifying off, on in [0, 1]
	DataChannel('SlideValveB', -1),  # -1 signifying off, on in [0, 1]
	DataChannel('SlideValveC', -1),  # -1 signifying off, on in [0, 1]
	DataChannel('SlideValveD', -1),  # -1 signifying off, on in [0, 1]
	DataChannel('EvaporatorA', 0),  # state of evaporators, {0, 1}
	DataChannel('EvaporatorB', 0),  # state of evaporators, {0, 1}
	DataChannel('EvaporatorC', 0),  # state of evaporators, {0, 1}
	DataChannel('EvaporatorD', 0),  # state of evaporators, {0, 1}
	DataChannel('EvaporatorE', 0),  # state of evaporators, {0, 1}
	DataChannel('TotalEvapDuty', 0),  # total evaporator duty
	DataChannel('CondenserFan', .5),  # condenser  duty
	DataChannel('alpha', 8),  # Transfer Coeff for Qin
	DataChannel('beta', 200),  # Transfer Coeff for Qout

]


## Helper Functions

def toPASCAL(psia): return 6894.76 * psia


def toCelsius(Kelvin): return Kelvin - 273.15


### Systems

def euler(x, xdot, dT): return x + xdot * dT


def timer(Time, DeltaT): return Time + DeltaT


def setQadded(Time):
	noise = 50 * np.cos(2 * np.pi * Time / 10) + 50 * np.random.random()
	return 600 + noise


def setRoomTemp(RoomTemp, Qadded, TotalQin, DeltaT):
	TRANSFERCOEFF = .005
	RoomTempDot = TRANSFERCOEFF * (Qadded - TotalQin)
	return euler(RoomTemp, RoomTempDot, DeltaT)


def setTotalVolumetricHighFlow(SlideValveA, SlideValveB, SlideValveC, SlideValveD):
	slides = [SlideValveA, SlideValveB, SlideValveC, SlideValveD]
	slideOn = [e for e in slides if e > 0]
	return (np.sum(slideOn) * .9 + len(slideOn) * .1) / len(slides)  # start up throughput around 10%


def setTotalEvapDuty(EvaporatorA, EvaporatorB, EvaporatorC, EvaporatorD, EvaporatorE):
	return np.sum([EvaporatorA, EvaporatorB, EvaporatorC, EvaporatorD, EvaporatorE])


def setTotalMassHighFlow(SuctionPressure, TotalVolumetricHighFlow):
	return CP.PropsSI('D', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia') * TotalVolumetricHighFlow


def setTotalQin(alpha, TotalMassLowFlow, TotalEvapDuty, RoomTemp, SuctionPressure):
	tempDiff = RoomTemp - toCelsius(CP.PropsSI('T', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia'))
	return alpha * TotalMassLowFlow * TotalEvapDuty * tempDiff


def setTotalQout(beta, TotalMassHighFlow, CondenserFan, AmbientTemp, DischargePressure):
	tempDiff = toCelsius(CP.PropsSI('T', 'P', toPASCAL(DischargePressure), 'Q', 1, 'Ammonia')) - AmbientTemp
	return beta * TotalMassHighFlow * CondenserFan * tempDiff


def setTotalCompressorPower(SlideValveA, SlideValveB, SlideValveC, SlideValveD, SuctionPressure):
	slides = [SlideValveA, SlideValveB, SlideValveC, SlideValveD]
	slideOn = [e for e in slides if e > 0]
	power = np.sum(slideOn) * 100 + len(slideOn) * 75  # rough estimate of Compressor Power
	perc = 1 + (18 - SuctionPressure) / 50  # 2%/psig efficiency gain with higher suction pressure
	return perc * power


def setSuctionPressure(SuctionPressure, TotalVolumetricHighFlow, TotalQin, DeltaT):
	DECAY = .5
	VF = TotalVolumetricHighFlow
	Q = TotalQin
	eqSP = 15 * (1 - VF) ** 4 + Q * (1.5 - VF) / 80 + 8
	spDot = DECAY * (eqSP - SuctionPressure)
	return euler(SuctionPressure, spDot, DeltaT)


## Feedback Controllers

def feedbackSlideValves(SuctionPressure):
	sp = SuctionPressure
	if sp < 10:
		duty = 0
	elif sp < 30:
		duty = (sp - 10) / 20
	else:
		duty = 1

	slides = [-1, -1, -1, -1]

	for i, _ in enumerate(slides):
		if duty > .025:
			slides[i] = min(1, (duty - .025) / .1)
			duty = duty - slides[i] * .225 - .025

	return slides


def feedbackEvaporatorOn(RoomTemp):
	if RoomTemp < -.5:
		N = 0
	else:
		N = 5 * (RoomTemp + .5)

	return [1 if i < N else 0 for i in range(5)]


# Optimization Controllers

def optSlideValves():
	pass


def optEvaporatorOn():
	pass


## Configure Systems

posters = [
	['timer', ['Time', 'DeltaT'], ['Time'], timer],
	func2Poster('Qadded', setQadded),
	func2Poster('RoomTemp', setRoomTemp),
	func2Poster('TotalVolumetricHighFlow', setTotalVolumetricHighFlow),
	func2Poster('TotalEvapDuty', setTotalEvapDuty),
	func2Poster('TotalMassHighFlow', setTotalMassHighFlow),
	func2Poster('TotalQin', setTotalQin),
	func2Poster('TotalQout', setTotalQout),
	func2Poster('TotalCompressorPower', setTotalCompressorPower),
	func2Poster('SuctionPressure', setSuctionPressure),
	['SlideValveSys', ['SuctionPressure'], ['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'],
	 feedbackSlideValves],
	['EvaporatorSys', ['RoomTemp'], ['EvaporatorA', 'EvaporatorB', 'EvaporatorC', 'EvaporatorD', 'EvaporatorE'],
	 feedbackEvaporatorOn]
]

## Run Simulation
refSim = TimedSimulation(posters, channels)
refSim.runSim(20)
refSim.plotVals(
	[['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'], ['TotalCompressorPower'], ['SuctionPressure'],
	 ['RoomTemp'], ['Qadded', 'TotalQin']])

## Animation
testSim = BaseSimulation(posters, channels)

cBody = Compressor(channel=None, pos=(0.6,0.05), size=(0.25,0.5), numCompressors=4)
ca = Compressors(channels[13], cBody)
cb = Compressors(channels[14], cBody)
cc = Compressors(channels[15], cBody)
cd = Compressors(channels[16], cBody)

eBody = Evaporator(channel=None, pos=(.15, -.15), size=(.3, .3), numEvaporators=5)
ea = Evaporators(channels[17], eBody)
eb = Evaporators(channels[18], eBody)
ec = Evaporators(channels[19], eBody)
ed = Evaporators(channels[20], eBody)
ee = Evaporators(channels[21], eBody)

v = Vessel(channel=channels[4], pos=(.22, .3), size=(.2, .2))

cond = Condenser(channel=None, pos=(.6, 0.7), size=(0.25, 0.1))

expn = ExpansionValve(channel=None, pos=(.3, 0.625), size=(0.03, 0.07))

qin = HeatIn(channel=channels[8], pos=(0.3, -0.425))

qout = HeatOut(channel=channels[9], pos=(0.725, 0.85))

arw = PathArrows(v, cBody, cond, expn, eBody)

a = Animator([cBody, ca, cb, cc, cd, eBody, ea, eb, ec, ed, ee, v, cond, expn, qin, qout, arw], testSim, [0.1, 1], [-0.85, 1.2])
a.animate(10)
a.runAnimation(100, 20)
