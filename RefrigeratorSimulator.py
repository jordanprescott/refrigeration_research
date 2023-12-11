from SystemEvents import *
import numpy as np
Simulator = SystemsHandler()
import CoolProp.CoolProp as CP

### CHANNELS

channels = [
    DataChannel('Time', 0),
    DataChannel('DeltaT', 1),
    DataChannel('RoomTemp', 0),
    DataChannel('AmbientTemp', 22),
    DataChannel('SuctionPressure', 18),
    DataChannel('DischargePressure', 180),
    DataChannel('TotalCompressorPower', 300),
    DataChannel('Qadded', 0),
    DataChannel('TotalQin', 600),
    DataChannel('TotalQout', 900),
    DataChannel('TotalVolumetricFlow', .5),
    DataChannel('TotalMassFlow', 1),
    DataChannel('SlideValves', [-1, -1, -1, -1]),  # -1 signifying off
    DataChannel('EvaporatorOn', [0, 0, 0, 0, 0]),
    DataChannel('CondenserFan', .5),
    DataChannel('EvaporatorFan', .5),
    DataChannel('IsentropicEff', [.63, .63, .63, .63]),
]


### Systems

def euler(x, xdot, dT): return x + xdot * dT

def timer(Time, DeltaT): return [Time + DeltaT]

def fluctuateQadded(): return 50 * np.random.random() + 50

def setRoomTemp(RoomTemp, Qadded, Qin, DeltaT):
    TRANSFERCOEFF = .01
    RoomTempDot = TRANSFERCOEFF * (Qadded - Qin)
    return euler(RoomTemp, RoomTempDot, DeltaT)

def toPASCAL(psia): return 6894.76 * psia

def toCelsius(kelvin): return kelvin - 273.15

# probably wrong
def setTotalMassFlow(TotalMassFlow, TotalVolumetricFlow):
    temp = CP.PropsSI('D', 'P', toPASCAL(channels[4].value), 'Q', 1, 'Ammonia') * TotalVolumetricFlow
    if temp == TotalMassFlow:
        channels[11] = temp
    else:
        channels[11] = TotalMassFlow


ALPHA = 41.0           # [35, 45] Transfer Coefficient
BETA = 330.0           # [300, 400] Transfer Coefficient
MLOW = 1.0             # Normalize Mass Flow on Low Side
EFF = .63              # Isentropic Efficiency

# fix
qin = ALPHA * MLOW * channels[15].value * (channels[2].value - toCelsius(CP.PropsSI('T', 'P',
        toPASCAL(channels[4].value), 'Q', 1, 'Ammonia')))

# fix
qout = BETA * MHIGH * channels[14].value * (toCelsius(CP.PropsSI('T', 'P',
        toPASCAL(channels[5].value), 'Q', 1, 'Ammonia')) - channels[3].value)


systems = [
    ['timer', ['Time', 'DeltaT'], ['Time'], timer],
    # ['timer', ['Time', 'deltaT'], ['Time'], time]
    # ['timer', ['Time', 'deltaT'], ['Time'], time]
]



### Run Simulation

T = 10
history = []

for channel in channels:
    Simulator.addChannel(channel)

for system in systems:
    Simulator.registerSystem(*system)

history.append(list(Simulator.globalState().values()))
for t in range(T):
    [P.update() for P in Simulator.posters]
    [P.post() for P in Simulator.posters]

    history.append(list(Simulator.globalState().values()))

print(history)


##### Random Scripts
