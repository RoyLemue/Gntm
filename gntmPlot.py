#   Erstellt von Roy Ledermüller mit PyCharm Community Edition 
#   Erstelldatum:   22.01.2017
#   Projektname:    gntm
#   Getestet mit Python 3.5

import sys
import matplotlib.pyplot as plt
import numpy as np
import math

folgen = 13.0
userCount = 10
startAktien = 100.0
dividende = 1.2 # 5 Aktien generieren eine Neue
modelCount = 33
startwert = 10.0
aktien = userCount*startAktien*dividende**folgen
aktienScale = 2.0
umbruch = math.exp(1)*startAktien*userCount
umbruch = 1000
aktienMean = userCount * startAktien * dividende ** folgen

# Gelddividende =2.0, nach Top 10 =4.0


def main():
    # parse command line options


    x = np.linspace(0.0, 4000, 100000)
    vfunc = np.vectorize(modelValueFunction)
    out1 = startwert*vfunc(x)
    plt.plot(x, out1)
    plt.show()


def modelValueFirst(x):
    return np.exp(x * modelCount / (aktienScale * aktienMean))


def modelValueSecond(x):
    return startwert - startwert * np.exp(-x * modelCount / (aktienScale * aktienMean))


def modelValueFunction(x):
    if x < umbruch:
        value = modelValueFirst(x)
    else:
        value = (startwert - modelValueFirst(umbruch)) / (startwert - modelValueSecond(umbruch)) * (
            modelValueSecond(x) - modelValueSecond(umbruch)) + modelValueFirst(umbruch)
    return value

if __name__ == "__main__":
    main()