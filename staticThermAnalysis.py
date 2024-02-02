import numpy as np
import CoolProp.CoolProp as CP
from scipy.optimize import root
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression


#  Helper Functions

def toPASCAL(psia): return 6894.76 * psia

def toCelsius(Kelvin): return Kelvin - 273.15


# Thermodynamic Parameters

class CycleParams:
    def __init__(self):
        self.SP: float = 18       # [14, 25] psia
        self.DP: float = 150      # [150, 250] psia
        self.TROOM: float = 0     # [-5, 5] Celsius
        self.TAMB: float = 22     # [0, 35] Celsius
        self.MLOW = 1             # Normalized Mass Flow on Low Side

        self.COMPDUTY = .5   
        self.EVAPDUTY = .5
        self.CONDUTY  = .5

        self.ALPHA = self.getCoeff(self.Qin, 5000, 10)
        self.BETA = self.getCoeff(self.Qout, 6600, 10)
        self.EFF = self.getCoeff(self.Power, 1600, .5)

    def Qin(self, alpha=None):
        if alpha is None:
            alpha = self.ALPHA
        tempDiff = self.TROOM - toCelsius(CP.PropsSI('T', 'P', toPASCAL(self.SP), 'Q', 1, 'Ammonia'))
        return alpha * self.MLOW * self.EVAPDUTY * tempDiff
    
    def mHigh(self):
        return CP.PropsSI('D', 'P', toPASCAL(self.SP), 'Q', 1, 'Ammonia') * self.COMPDUTY
    
    def Qout(self, beta=None):
        if beta is None:
            beta = self.BETA
        tempDiff = toCelsius(CP.PropsSI('T', 'P', toPASCAL(self.DP), 'Q', 1, 'Ammonia')) - self.TAMB
        return beta * self.mHigh() * self.CONDUTY * tempDiff
    
    def Power(self, eff=None):
        if eff is None:
            eff = self.EFF
        h1 = CP.PropsSI('H', 'P', toPASCAL(self.SP), 'Q', 1, 'Ammonia')
        s = CP.PropsSI('S', 'P', toPASCAL(self.SP), 'Q', 1, 'Ammonia')
        h2 = CP.PropsSI('H', 'P', toPASCAL(self.DP), 'S', s, 'Ammonia')  # assume isoentropic compression
        return self.mHigh() * (h2 - h1) * (1/eff) / 1000  # kW

    def getCoeff(self, func, VAL, guess):
        def fixedFunc(param):
            return func(param) - VAL
        
        sol = root(fixedFunc, guess)
        if sol.success:
            return sol.x[0]
        else:
            print('No solution found for {} and value {}.'.format(func.__name__, VAL))


## Analysis 


def fixedPointFunc(cParams):
    def f(sp):
        cParams.SP = sp
        qin = cParams.Qin()
        qout = cParams.Qout()
        power = cParams.Power()
        return qin + power - qout
    return f


def getPoints():
    CP = CycleParams()
    print('COEFFICIENTS: ', CP.ALPHA, CP.BETA, CP.EFF)
    spData = np.zeros((46, 46))
    qinData = np.zeros((46, 46))
    cDutyData = np.zeros((46, 46))

    for i, compDuty in enumerate(np.arange(0.1, 1.01, .02)):
        for j, evapDuty in enumerate(np.arange(0.1, 1.01, .02)):
            
            CP.COMPDUTY = compDuty
            CP.EVAPDUTY = evapDuty
            
            sol = root(fixedPointFunc(CP), 18)
            
            if sol.success:
                sp = sol.x[0]
                CP.SP = sp
                spData[i, j] = sp
                cDutyData[i, j] = compDuty
                qinData[i, j] = CP.Qin()

    return spData, qinData, cDutyData


def reshapeData(spData, cDutyData, qinData):
    SP = spData.flatten()
    QIN = qinData.flatten()
    CD = cDutyData.flatten()
    
    X = np.vstack((CD, QIN)).T
    y = SP
    return X, y

def polyFit(X, y, deg=1):
    poly = PolynomialFeatures(degree=deg)
    Xpoly = poly.fit_transform(X)
    reg = LinearRegression(fit_intercept=False).fit(Xpoly, y)
    print('fit: ', reg.score(Xpoly, y))
    return reg.coef_

# Plotting
    
def gen3d(cDutyData, qinData, coef, deg):
    poly = PolynomialFeatures(degree=deg)
    spData = np.zeros((46, 46))
    for i in range(46):
        for j in range(46):
            spData[i, j] = np.dot(poly.fit_transform([[cDutyData[i, j], qinData[i, j]]]), coef)[0]
    return spData

def plot3d(spDatas, cDutyData, qinData):
    import matplotlib.pyplot as plt
    from matplotlib import cm

    _, ax = plt.subplots(subplot_kw={"projection": "3d"})
    cmaps = [cm.Blues, cm.Reds, cm.Purples, cm.Greens, cm.Oranges, cm.Greys]

    for i, spD in enumerate(spDatas):  # expect multiple sp Datas
        ax.plot_surface(cDutyData, qinData, spD, cmap=cmaps[i])
    plt.show()


if __name__ == '__main__':
    spData, qinData, cDutyData = getPoints()
    print('generated points')
    X, y = reshapeData(spData, cDutyData, qinData)
    coef = polyFit(X, y, deg=2)
    spDatafit = gen3d(cDutyData, qinData, coef, 2)
    print([round(c, 4) for c in coef])
    plot3d([spData, spDatafit], cDutyData, qinData)
