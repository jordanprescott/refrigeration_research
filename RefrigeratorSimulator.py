from SystemEvents import *
import numpy as np
import CoolProp.CoolProp as CP
from staticThermAnalysis import toCelsius, toPASCAL
from sklearn.preprocessing import PolynomialFeatures

### CHANNELS

channels = [
	DataChannel('Time', 0),  # minutes
	DataChannel('DeltaT', 10),  # minutes
	DataChannel('RoomTemp', 0),  # Celsius
	DataChannel('AmbientTemp', 22),  # Celsius
	DataChannel('SuctionPressure', 18),  # psia
	DataChannel('DischargePressure', 150),  # psia
	DataChannel('TotalCompressorPower', 1600),  # kW
	DataChannel('TotalEnergy', 0),  # kWh
	DataChannel('Qadded', 2000),  # kW 
	DataChannel('TotalQin', 5000),  # kW
	DataChannel('TotalQout', 6600),  # kW
	DataChannel('TotalMassHighFlow', 1),  # kg/min (normalized not realized)
	DataChannel('TotalMassLowFlow', 1),  # kg/min  (normalized not realized)
    DataChannel('CondenserFan', .5),  # Condenser  Fan Speed
    GroupChannel('SlideValves', [DataChannel('SlideValveA', 1), 
                                 DataChannel('SlideValveB', 1), 
                                 DataChannel('SlideValveC', -1), 
                                 DataChannel('SlideValveD', -1)]),  # -1 signifying off, on in [0, 1]
	GroupChannel('EvaporatorsOn', [DataChannel('EvaporatorA', 1),
                                   DataChannel('EvaporatorB', 1),
                                   DataChannel('EvaporatorC', 1),
                                   DataChannel('EvaporatorD', 0),
                                   DataChannel('EvaporatorE', 0)])  # on/off state of evaporators, in {0, 1}
]
channels = fillOutChannels(channels)


## Helper Functions

def toMin(day): return day * 24 * 60

def CompressorDuty(SlideValves):
	# Total Compressor Duty given slide valves
	slideOn = [e for e in SlideValves if e > 0]
	return (np.sum(slideOn) * .9 + len(slideOn) * .1) / len(SlideValves)  # capacity at 0% slide valve is around 10%

# Fitted SP Response Curve: equilibrium suction pressure given compressor duty and Qin
polySP = PolynomialFeatures(degree = 2)
coeff = np.array([26.6693779, -92.8539095, .00673208269, 70.5264337, -.00463903315, 0])
def eqSuction(CDuty, Qin):
	Xpoly = polySP.fit_transform([[CDuty, Qin]])
	return np.dot(Xpoly, coeff)[0]


### Systems

def euler(x, xdot, dT): return x + xdot * dT

def timer(Time, DeltaT): return Time + DeltaT

def setQadded(Time):
	# comes from Q calculations
	return 4000 - 2000 * np.cos(2 * np.pi * Time / toMin(2))**4 + 500 * np.random.random()

def setRoomTemp(RoomTemp, Qadded, TotalQin, DeltaT):
	TRANSFERCOEFF = 1 / toMin(1) / 4000  # 1 deg change over day based on flywheeling experiment + ~4000 Qadded to system
	RoomTempDot = TRANSFERCOEFF * (Qadded - TotalQin)
	return euler(RoomTemp, RoomTempDot, DeltaT)

def setTotalMassHighFlow(SuctionPressure, SlideValves):
	return CP.PropsSI('D', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia') * CompressorDuty(SlideValves)

def setTotalQin(TotalMassLowFlow, EvaporatorsOn, RoomTemp, SuctionPressure):
	ALPHA = 342
	
	tempDiff = RoomTemp - toCelsius(CP.PropsSI('T', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia'))
	return ALPHA * TotalMassLowFlow * sum(EvaporatorsOn)/len(EvaporatorsOn) * tempDiff

def setTotalQout(TotalMassHighFlow, CondenserFan, AmbientTemp, DischargePressure):
	BETA = 6122
	
	tempDiff = toCelsius(CP.PropsSI('T', 'P', toPASCAL(DischargePressure), 'Q', 1, 'Ammonia')) - AmbientTemp
	return BETA * TotalMassHighFlow * CondenserFan * tempDiff

def setTotalCompressorPower(SlideValves, SuctionPressure):
	ONPOWER = 600         # 40% power from turning on
	SLIDEPOWER = 1000     # COP = 3 (ref/power = 3)
	SPSET = 18           # 2% efficiency gain with 
	GAIN = .02           # each degree higher suction temperature after 18 psi
	
	slideOn = [e for e in SlideValves if e > 0]
	power = np.sum(slideOn) * SLIDEPOWER + len(slideOn) * ONPOWER  
	SPdiff = CP.PropsSI('T', 'P', toPASCAL(SPSET), 'Q', 1, 'Ammonia') - CP.PropsSI('T', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia')
	perc = 1 - SPdiff * GAIN  # 2%/psig efficiency gain with higher suction pressure after 18 psi
	return perc * power

def setTotalEnergy(TotalEnergy, TotalCompressorPower, DeltaT):
	return euler(TotalEnergy, TotalCompressorPower, DeltaT/60) # conversion from minutes to hours

def setSuctionPressure(SuctionPressure, SlideValves, TotalQin, DeltaT):
	DECAY = .003
	eqSP = eqSuction(CompressorDuty(SlideValves), TotalQin)
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
	K = 5
	if RoomTemp < -.5:
		N = 0
	else:
		N = K * (RoomTemp + .5)

	return [1 if i < N else 0 for i in range(5)]


# Optimization Controllers
import mip

def optController(SuctionPressure, RoomTemp, Qadded, SlideValves):	
	T = 10 # Horizon
	n = 4 # number of compressors
	m = 5 # number of evaporators
	ONPOWER = 600
	SLIDEPOWER = 1000
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
	power = mip.xsum([ONPOWER * o[i, j] + SLIDEPOWER * s[i, j] for i in range(T) for j in range(n)])   # compressor power
	# switchComp = mip.xsum([o[i, j] - o[i - 1, j] for i in range(1, T) for j in range(n)])  # switching cost for compressors
	# switchEvap = mip.xsum([e[i, j] - e[i - 1, j] for i in range(1, T) for j in range(n)])  # switching cost for evaporators
	SPcost = mip.xsum([spAbs[i] for i in range(T)])
	M.objective = mip.minimize(power + lamb1 * SPcost)

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
	refSim.runSim(toMin(3))
	refSim.plotVals([['Qadded'], ['RoomTemp'], ['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'], ['TotalCompressorPower'], ['SuctionPressure'],
				 ['RoomTemp'], ['Qadded', 'TotalQin']])