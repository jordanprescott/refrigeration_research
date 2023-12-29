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
    noise = 50 * np.cos(2 * np.pi * Time / 10 ) + 50 * np.random.random()
    return 600 + noise

def setRoomTemp(RoomTemp, Qadded, TotalQin, DeltaT):
    TRANSFERCOEFF = .005
    RoomTempDot = TRANSFERCOEFF * (Qadded - TotalQin)
    return euler(RoomTemp, RoomTempDot, DeltaT)

def setTotalVolumetricHighFlow(SlideValveA, SlideValveB, SlideValveC, SlideValveD):
    slides = [SlideValveA, SlideValveB, SlideValveC, SlideValveD]
    slideOn = [e for e in slides if e > 0]
    return (np.sum(slideOn) * .9 + len(slideOn) * .1)/len(slides)  # start up throughput around 10%

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
    perc = 1 + (18 - SuctionPressure)/50 # 2%/psig efficiency gain with higher suction pressure
    return perc * power

def setSuctionPressure(SuctionPressure, TotalVolumetricHighFlow, TotalQin, DeltaT):
    DECAY = .5
    VF = TotalVolumetricHighFlow
    Q = TotalQin
    eqSP = 15 * (1-VF)**4 + Q * (1.5 - VF)/80 + 8
    spDot = DECAY * (eqSP - SuctionPressure)
    return euler(SuctionPressure, spDot, DeltaT)


## Feedback Controllers

def feedbackSlideValves(SuctionPressure):
    sp = SuctionPressure
    if sp < 10:
        duty = 0
    elif sp < 30:
        duty = (sp - 10)/20
    else:
        duty = 1

    slides = [-1, -1, -1, -1]
    
    for i, _ in enumerate(slides):
        if duty > .025:
            slides[i] = min(1, (duty-.025)/.1)
            duty = duty - slides[i]*.225 - .025
    
    return slides

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
    ['SlideValveSys', ['SuctionPressure'], ['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'], feedbackSlideValves],
    ['EvaporatorSys', ['RoomTemp'], ['EvaporatorA', 'EvaporatorB', 'EvaporatorC', 'EvaporatorD', 'EvaporatorE'], feedbackEvaporatorOn]
]

### Run Simulation
refSim = TimedSimulation(posters, channels)
refSim.runSim(20)
refSim.plotVals([['SlideValveA', 'SlideValveB', 'SlideValveC', 'SlideValveD'], ['TotalCompressorPower'], ['SuctionPressure'], ['RoomTemp'], ['Qadded', 'TotalQin']])

#################
