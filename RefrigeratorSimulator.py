from SystemEvents import *
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
    DataChannel('alpha', 8), # Transfer Coeff for Qin
    DataChannel('beta', 200),  # Transfer Coeff for Qout

]

## Helper Functions

def toPASCAL(psia): return 6894.76 * psia

def toCelsius(Kelvin): return Kelvin - 273.15

### Systems

def euler(x, xdot, dT): return x + xdot * dT

def timer(Time, DeltaT): return Time + DeltaT

def setQadded(Time): 
    noise = 100 * np.cos(2 * np.pi * Time / 10 ) + 40 * np.random.random() - 20
    return 600 + noise

def setRoomTemp(RoomTemp, Qadded, TotalQin, DeltaT):
    TRANSFERCOEFF = .0025
    RoomTempDot = TRANSFERCOEFF * (Qadded - TotalQin)
    return euler(RoomTemp, RoomTempDot, DeltaT)

def setTotalVolumetricHighFlow(SlideValveA, SlideValveB, SlideValveC, SlideValveD):
    slides = [SlideValveA, SlideValveB, SlideValveC, SlideValveD]
    slideOn = [e for e in slides if e > 0]
    return (np.sum(slideOn) * .8 + len(slideOn) * .2)/len(slides)  # start up throughput around 20%

def setTotalEvapDuty(EvaporatorA, EvaporatorB, EvaporatorC, EvaporatorD, EvaporatorE):
    return np.sum([EvaporatorA, EvaporatorB, EvaporatorC, EvaporatorD, EvaporatorE])

def setTotalMassHighFlow(SuctionPressure, TotalVolumetricFlow):
    return CP.PropsSI('D', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia') * TotalVolumetricFlow

def setTotalQin(alpha, TotalMassLowFlow, EvaporatorOn, RoomTemp, SuctionPressure):
    tempDiff = RoomTemp - toCelsius(CP.PropsSI('T', 'P', toPASCAL(SuctionPressure), 'Q', 1, 'Ammonia'))
    return alpha * TotalMassLowFlow * np.sum(EvaporatorOn) * tempDiff

def setTotalQout(beta, TotalMassHighFlow, CondenserFan, AmbientTemp, DischargePressure):
    tempDiff = toCelsius(CP.PropsSI('T', 'P', toPASCAL(DischargePressure), 'Q', 1, 'Ammonia')) - AmbientTemp
    return beta * TotalMassHighFlow * CondenserFan * tempDiff

def setTotalCompressorPower(SlideValves, SuctionPressure):
    slideOn = [e for e in SlideValves if e > 0]
    power = np.sum(slideOn) * 100 + len(slideOn) * 10  # rough estimate of Compressor Power 
    perc = 1 + (18 - SuctionPressure)/50 # 2%/psig efficiency gain with higher suction pressure
    return perc * power

def setSuctionPressure(TotalVolumetricFlow, TotalQin):
    # evapDuty = np.sum(EvaporatorOn)/5
    # norm = (TotalVolumetricFlow**2 + evapDuty**2)**.5
    # return [18 - 15*(TotalVolumetricFlow - evapDuty)/norm] # coming from thermo models
    return 18


## Feedback Controllers

def feedbackSlideValves(Time): #SuctionPressure):
    a = .1 * np.cos(2 * np.pi * Time / 10 )
    return [a+.5, a+.6, a+.7, a+.8]

def feedbackEvaporatorOn(RoomTemp):
    if RoomTemp < -.5:
        N = 0
    else:
        N = 5 * (RoomTemp  + .5)
    
    return [1 if i < N else 0 for i in range(5)]

# Optimization Controllers

def optSlideValves():
    pass

def optEvaporatorOn():
    pass

## Configure Systems

systems = [
    ['timer', ['Time', 'DeltaT'], ['Time'], timer],
    ['Qadder', ['Time'], ['Qadded'], setQadded],
    #['roomTempSys', ['RoomTemp', 'Qadded', 'TotalQin', 'DeltaT'], ['RoomTemp'], setRoomTemp],
    ['TotalVolumetricHighFlowSys', ['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'], ['TotalVolumetricHighFlow'], setTotalVolumetricHighFlow],
    ['TotalEvapDutySys', ['EvaporatorA', 'EvaporatorB', 'EvaporatorC', 'EvaporatorD', 'EvaporatorE'], ['TotalEvapDuty'], setTotalEvapDuty],
    ['TotalMassHighFlowSys', ['SuctionPressure', 'TotalVolumetricHighFlow'], ['TotalMassHighFlow'], setTotalMassHighFlow],
    ['TotalQinSys', ['alpha', 'TotalMassLowFlow', 'TotalEvapDuty', 'RoomTemp', 'SuctionPressure'], ['TotalQin'], setTotalQin],
    ['TotalQoutSys', ['beta', 'TotalMassHighFlow', 'CondenserFan', 'AmbientTemp', 'DischargePressure'], ['TotalQout'], setTotalQout],
    # ['TotalCompressorPowerSys', ['SlideValves', 'SuctionPressure'], ['TotalCompressorPower'], setTotalCompressorPower],
    #['SuctionPressureSys', ['TotalVolumetricFlow', 'TotalQin'], ['SuctionPressure'], setSuctionPressure],
    ['SlideValveSys', ['Time'], ['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'], feedbackSlideValves],
    ['EvaporatorSys', ['RoomTemp'], ['EvaporatorA', 'EvaporatorB', 'EvaporatorC', 'EvaporatorD', 'EvaporatorE'], feedbackEvaporatorOn]
]

### Run Simulation
# refSim = TimedSimulation(systems, channels)
# refSim.runSim(10)
# refSim.plotVals([['Qadded', 'TotalQin'], ['RoomTemp']])

#################

def func2Poster(func):
    from inspect import signature
    
    name = func.__name__[3:]  # assuming 'set{Parameter Name}'
    return ['{}Sys'.format(name), list(signature(func).parameters), [name], func]


funcs = [setQadded, setRoomTemp, setTotalVolumetricHighFlow, setTotalEvapDuty, setTotalMassHighFlow, setTotalQin, setTotalQout, setTotalCompressorPower]

for f in funcs:
    print(func2Poster(f))