from SystemEvents import *
import numpy as np
import CoolProp.CoolProp as CP

### CHANNELS

channels = [
	DataChannel('Time', 0),  # minutes
	DataChannel('DeltaT', .05),  # minutes
	DataChannel('RoomTemp', 0),  # Celsius
	DataChannel('AmbientTemp', 22),  # Celsius
	DataChannel('SuctionPressure', 18),  # psia
	DataChannel('DischargePressure', 180),  # psia
	DataChannel('TotalCompressorPower', 300),  # kW
	DataChannel('TotalEnergy', 0),  # kWh
	DataChannel('Qadded', 600),  # kW 
	DataChannel('TotalQin', 600),  # kW
	DataChannel('TotalQout', 1000),  # kW
	DataChannel('TotalVolumetricHighFlow', .5),  # m^3/m
	DataChannel('TotalMassHighFlow', 1),  # kg/m
	DataChannel('TotalMassLowFlow', 1),  # kg/m
    DataChannel('CondenserFan', .5),  # Condenser  Fan Speed
    GroupChannel('SlideValves', [DataChannel('SlideValveA', -1), 
                                 DataChannel('SlideValveB', -1), 
                                 DataChannel('SlideValveC', -1), 
                                 DataChannel('SlideValveD', -1)]),  # -1 signifying off, on in [0, 1]
	GroupChannel('EvaporatorsOn', [DataChannel('EvaporatorA', 0),
                                   DataChannel('EvaporatorB', 0),
                                   DataChannel('EvaporatorC', 0),
                                   DataChannel('EvaporatorD', 0),
                                   DataChannel('EvaporatorE', 0)])  # on/off state of evaporators, in {0, 1}
]
channels = fillOutChannels(channels)

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

def setTotalVolumetricHighFlow(SlideValves):
	slideOn = [e for e in SlideValves if e > 0]
	return (np.sum(slideOn) * .9 + len(slideOn) * .1) / len(SlideValves)  # start up throughput around 10%

def setTotalMassHighFlow(SuctionPressure, TotalVolumetricHighFlow):
	return CP.PropsSI('D', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia') * TotalVolumetricHighFlow

def setTotalQin(TotalMassLowFlow, EvaporatorsOn, RoomTemp, SuctionPressure):
	ALPHA = 8
	tempDiff = RoomTemp - toCelsius(CP.PropsSI('T', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia'))
	return ALPHA * TotalMassLowFlow * sum(EvaporatorsOn) * tempDiff

def setTotalQout(TotalMassHighFlow, CondenserFan, AmbientTemp, DischargePressure):
	BETA = 200
	tempDiff = toCelsius(CP.PropsSI('T', 'P', toPASCAL(DischargePressure), 'Q', 1, 'Ammonia')) - AmbientTemp
	return BETA * TotalMassHighFlow * CondenserFan * tempDiff

def setTotalCompressorPower(SlideValves, SuctionPressure):
	slideOn = [e for e in SlideValves if e > 0]
	power = np.sum(slideOn) * 100 + len(slideOn) * 75  # rough estimate of Compressor Power
	perc = 1 + (18 - SuctionPressure) / 50  # 2%/psig efficiency gain with higher suction pressure
	return perc * power

def setTotalEnergy(TotalEnergy, TotalCompressorPower, DeltaT):
	return euler(TotalEnergy, TotalCompressorPower, DeltaT/60) # conversion from minutes to hours

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
import mip

def optController(SuctionPressure, RoomTemp, Qadded):	
	T = 10 # Horizon
	n = 4 # number of compressors
	m = 5 # number of evaporators
	lamb1 = 40
	lamb2 = 0
	lamb3 = 0
	M = mip.Model()
	M.verbose = 0

	# variables
	s = M.add_var_tensor((T, n), 's', ub=1) # slide valves in [0, 1]
	o = M.add_var_tensor((T, n), 'o', var_type=mip.BINARY) # on/off comp in {0, 1}
	e = M.add_var_tensor((T, m), 'e', var_type=mip.BINARY) # on/off evap in {0, 1}
	# swO = M.add_var_tensor((T-1, n), 'swO') # switch comp
	sp = M.add_var_tensor((T,), 'sp', lb=float('-inf')) # suction pressure for each time
	spAbs = M.add_var_tensor((T,), 'spAbs') # suction pressure for each time
	Tmp =  M.add_var_tensor((T,), 'Tmp', lb=float('-inf')) # temperature for each time

	# objectives
	power = mip.xsum([75 * o[i, j] + 100 * s[i, j] for i in range(T) for j in range(n)])   # compressor power
	switchComp = mip.xsum([o[i, j] - o[i - 1, j] for i in range(1, T) for j in range(n)])  # switching cost for compressors
	switchEvap = mip.xsum([e[i, j] - e[i - 1, j] for i in range(1, T) for j in range(n)])  # switching cost for evaporators
	SPcost = mip.xsum([spAbs[i] for i in range(T)])
	M.objective = mip.minimize(power + lamb1 * SPcost + lamb2 * switchComp + lamb3 * switchEvap)

	TempDiff = RoomTemp - toCelsius(CP.PropsSI('T', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia'))
	B = 6.5 * TempDiff
	Qin = [B * mip.xsum([e[i, j] for j in range(m)]) for i in range(T)]
	Duty = [mip.xsum([(.1 * o[i, j] + .9 * s[i, j])/n for j in range(n)]) for i in range(T)]
	spEq = [.0202 * Qin[i] - 31.7623 * Duty[i] + 24.6082 for i in range(T)]  # from fitting via thermo dynamic analysis

	# dynamics
	DEC = .5
	TRN = .005
	TMPSET = 0

	M += sp[0] == SuctionPressure
	M += Tmp[0] == RoomTemp
	for i in range(T-1):
		M += sp[i+1] == DEC * sp[i] + (1-DEC) * spEq[i]
		M += Tmp[i+1] == Tmp[i] + TRN * (Qadded - Qin[i])
		M += Tmp[i+1] <= TMPSET

	# constraints
	SPSET = 18
	for i in range(T):
		M += spAbs[i] >= sp[i] - SPSET
		for j in range(n):
			M += s[i, j] <= o[i, j] * 1

	if M.optimize() == mip.OptimizationStatus.OPTIMAL:
		compressors = [s[0, j].x if o[0, j].x > 0 else -1 for j in range(n)]
		evaporators = [e[0, j].x for j in range(m)]
	else:
		print('Optimization failed')
		compressors = [-1] * n
		evaporators = [0] * n
	
	M.clear()
	return [compressors, evaporators]

## Configure Systems

posters = [
	['timer', ['Time', 'DeltaT'], ['Time'], timer],
	func2Poster('Qadded', setQadded),
	func2Poster('RoomTemp', setRoomTemp),
	func2Poster('TotalVolumetricHighFlow', setTotalVolumetricHighFlow),
	func2Poster('TotalMassHighFlow', setTotalMassHighFlow),
	func2Poster('TotalQin', setTotalQin),
	func2Poster('TotalQout', setTotalQout),
	func2Poster('TotalCompressorPower', setTotalCompressorPower),
	func2Poster('TotalEnergy', setTotalEnergy),
	func2Poster('SuctionPressure', setSuctionPressure),
	['SlideValveSys', ['SuctionPressure'], ['SlideValves'], feedbackSlideValves],
	['EvaporatorSys', ['RoomTemp'], ['EvaporatorsOn'], feedbackEvaporatorOn]
	#['OptController', ['SuctionPressure', 'RoomTemp', 'Qadded'], ['SlideValves', 'EvaporatorsOn'], optController]
]


if __name__ == '__main__':
	# optController(18, 0, 600)
	# Run Simulation
	refSim = TimedSimulation(posters, channels)
	refSim.runSim(20)
	refSim.plotVals(
		[['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'], ['TotalCompressorPower'], ['SuctionPressure'],
		 ['RoomTemp'], ['Qadded', 'TotalQin']])