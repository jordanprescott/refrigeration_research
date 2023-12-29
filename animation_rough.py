import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle, Polygon, Wedge
import matplotlib.patches as mpatches
from matplotlib import colormaps
from matplotlib import cm
from matplotlib import animation


condenserX = [.7, 1, 1, .7, .7]
condenserY = [.9, .9, 1, 1, .9]

compressorX = [.6, 1.05, 1.05, .6, .6]
compressorY = [.35, .35, .65, .65, .35]

vesselX = [.05, .35, .35, .05, .05]
vesselY = [.4, .4, .6, .6, .4]

evaporatorX = [0, .4, .4, 0, 0]
evaporatorY = [0, 0, .25, .25, 0]

# plt.plot(rectangleX, rectangleY, 'o')
# plt.plot(condenserX, condenserY, '-')

# plt.plot(condenserX, condenserY, '-')
# plt.plot(compressorX, compressorY, '-')
# plt.plot(vesselX, vesselY, '-')
# plt.plot(evaporatorX, evaporatorY, '-')

fig, ax = plt.subplots()


def visualize(num_compressors, num_evaporators, q_in, q_out, c, e):


    condenser = np.array([
        [.65, .9],
        [1, .9],
        [1, 1],
        [.65, 1]
    ])

    compressor_body = np.array([
        [.6, .35],
        [1.05, .35],
        [1.05, .65],
        [.6, .65]
    ])

    vessel = np.array([
        [.05, .4],
        [.35, .4],
        [.35, .6],
        [.05, .6]
    ])

    evaporator_body = np.array([
        [0, 0],
        [.4, 0],
        [.4, .25],
        [0, .25]
    ])

    expansionvalve = np.array([
        [.175, .75],
        [.225, .75],
        [.2, .8],
        [.175, .85],
        [.225, .85]
    ])



    one_two = [(.35, .6), (.5, .5), 'black']
    two_three = [(.825, .825), (.65, .9), 'black']
    three_four = [(.65, .2, .2), (.95, .95, .85), 'black']
    four_one = [(.2, .2), (.75, .6), 'black']

    lower_loop = [(.2, .2), (.4, .25), 'black']
    lower_loop2 = [(.4, .45, .45, .3, .3), (.125, .125, .3, .3, .4), 'black']


    plt.text(.825, .95, 'Condenser', fontsize=10, va='center', ha='center')
    plt.text(.2, .5, 'Vessel', fontsize=10, va='center', ha='center')
    plt.text(.23, .8, 'Expansion Value', fontsize=10, va='center', ha='left')
    plt.text(.825, .2, 'Compressors', fontsize=10, va='center', ha='center')
    plt.text(.2, -.15, 'Evaporators', fontsize=10, va='center', ha='center')






    ax.add_patch(mpatches.Polygon(condenser, fill=False))
    ax.add_patch(mpatches.Polygon(compressor_body, fill=False))
    ax.add_patch(mpatches.Polygon(vessel, fill=False))
    ax.add_patch(mpatches.Polygon(evaporator_body, fill=False))
    ax.add_patch(mpatches.Polygon(expansionvalve, fill=True, color='black'))

    ax.plot(*one_two)
    ax.plot(*two_three)
    ax.plot(*three_four)
    ax.plot(*four_one)
    ax.plot(*lower_loop)
    ax.plot(*lower_loop2)


    scale = .2 # use to normalize qin and qout


    inferno_cm = (cm.inferno(range(256)))

    ax.arrow(.825, 1.05, 0, q_out * scale, shape='full', linewidth=3, head_width=.03, color=inferno_cm[round(q_out * 255)], label='1')
    ax.arrow(.2, -.3 - q_in * scale, 0, q_in * scale, shape='full', linewidth=3, head_width=.03, color=inferno_cm[round(q_in * 255)], label='1')


    plt.text(.825, 1.05 + q_out * scale / 2, '  Q out', fontsize=10, va='center', ha='left')
    plt.text(.2, -.3 - q_in * scale / 2, '  Q in', fontsize=10, va='center', ha='left')




    ax.arrow(one_two[0][0], one_two[1][0], (one_two[0][1]-one_two[0][0])/2, 0, shape='full', linewidth=.8, head_width=.025, color='black', label='1')
    ax.arrow(two_three[0][0], two_three[1][0], 0, (two_three[1][1]-two_three[1][0])/2, shape='full', linewidth=.8, head_width=.025, color='black', label='1')
    ax.arrow(three_four[0][0], three_four[1][0], (three_four[0][1]-three_four[0][0])/2, 0, shape='full', linewidth=.8, head_width=.025, color='black', label='1')
    ax.arrow(four_one[0][0], four_one[1][0], (four_one[0][1]-four_one[0][0])/2, 0, shape='full', linewidth=.8, head_width=.025, color='black', label='1')

    ax.arrow(lower_loop[0][0], lower_loop[1][0], 0, (lower_loop[1][1]-lower_loop[1][0])/2, shape='full', linewidth=.8, head_width=.025, color='black', label='1')
    ax.arrow(lower_loop2[0][2], lower_loop2[1][2], (lower_loop2[0][3]-lower_loop2[0][2])/2, 0, shape='full', linewidth=.8, head_width=.025, color='black', label='1')





    compressor_length = compressor_body[1, 0] - compressor_body[0, 0] - .025
    # compressor_length = compressorX[1] - compressorX[0]

    compressor_inds = []
    compressor_valves= []

    for i in range(num_compressors):
        compressor_individual = np.array([
            [compressor_body[0, 0] + .025 + compressor_length / num_compressors * i, .375], #bottom left, ccw
            [compressor_body[0, 0] + compressor_length / num_compressors*(i + 1), .375],
            [compressor_body[0, 0] + compressor_length / num_compressors*(i + 1), .625],
            [compressor_body[0, 0] + .025 + compressor_length / num_compressors * i, .625]
        ])
        # compressor_ind_X = []

        compressor_inds.append(compressor_individual.copy())
        compressor_valves.append(compressor_individual.copy())

        compressor_valves[i][0][1] = 0.375
        compressor_valves[i][1][1] = 0.375

        ax.add_patch(mpatches.Polygon(compressor_individual, fill=False))

        # ax.add_patch(mpatches.Polygon(compressor_valves[i], fill=False, color='black'))

        plt.text((compressor_individual[0][0] + (compressor_individual[1][0]-compressor_individual[0][0])/2), .3, 'C'+str(i+1), fontsize=10, va='center', ha='center')


    plt.text(compressor_body[1][0], compressor_individual[0][1], '- - - 0%', fontsize=10, va='center', ha='left')
    plt.text(compressor_body[1][0], compressor_individual[0][1] + (compressor_individual[2][1] - compressor_individual[0][1])/2, '  (Percent on)', fontsize=10, va='center', ha='left')
    plt.text(compressor_body[1][0], compressor_individual[2][1], '- - - 100%', fontsize=10, va='center', ha='left')




    for i in range(num_compressors):
        compressor_valves[i][2][1] = 0.375 + .25 * c[i]
        compressor_valves[i][3][1] = 0.375 + .25 * c[i]
        ax.add_patch(mpatches.Polygon(compressor_valves[i], fill=True))
        ax.add_patch(mpatches.Polygon(compressor_inds[i], fill=False, color='black'))





    evaporator_length = evaporator_body[1, 0] - evaporator_body[0, 0] - .025
    # compressor_length = compressorX[1] - compressorX[0]

    evaporator_valves = []

    for i in range(num_evaporators):
        evaporator_individual = np.array([
            [evaporator_body[0, 0] + .025 + evaporator_length / num_evaporators * i, 0.025], # bottom left corner, ccw
            [evaporator_body[0, 0] + evaporator_length / num_evaporators*(i + 1), 0.025],
            [evaporator_body[0, 0] + evaporator_length / num_evaporators*(i + 1), .225],
            [evaporator_body[0, 0] + .025 + evaporator_length / num_evaporators * i, .225]
        ])

        evaporator_valves.append(evaporator_individual.copy())

        evaporator_valves[i][0][1] = 0.025
        evaporator_valves[i][1][1] = 0.025


        # compressor_ind_X = []

        ax.add_patch(mpatches.Polygon(evaporator_individual, fill=False))


        # ax.add_patch(mpatches.Polygon(evaporator_valves[i], fill=False, color='black'))

        plt.text((evaporator_individual[0][0] + (evaporator_individual[1][0] - evaporator_individual[0][0]) / 2), -.05,
                 'E' + str(i + 1), fontsize=10, va='center', ha='center')



    plt.text(evaporator_body[0][0], evaporator_individual[0][1] + (evaporator_individual[2][1] - evaporator_individual[0][1])/2, '(White off, blue on)  ', fontsize=10, va='center', ha='right')




    for i in range(num_evaporators):
        ax.add_patch(mpatches.Polygon(evaporator_valves[i], fill=e[i], edgecolor='black'))


    ax.set_xlim(-0.3, 1.35)
    ax.set_ylim(-0.6, 1.4)

    return fig







def update(num_compressors, num_evaporators, q_in, q_out, c, e):
    visualize(num_compressors, num_evaporators, q_in, q_out, c, e)



compressor_states = [.3, .67, .4, .2]
evaporator_states = [1, 1, 1, 1, 0]

# visualize(4, 5, .8, .3, compressor_states, evaporator_states)
# plt.show()


s = 20

cl = [[0, 0, 0, 0],
      [.1, .05, .025, 0],
      [.2, .1, .05, 0],
      [.3, .15, .075, .25],
      [.4, .2, .1, .5],
      [.5, .25, .125, .75],
      [.6, .3, .15, 1],
      [.7, .35, .175, 1],
      [.8, .4, .2, 1],
      [.9, .45, .225, 1],
      [1, .5, .25, 1],
      [1, .55, .275, 1],
      [.9, .6, .3, .8],
      [.8, .65, .325, .8],
      [.7, .7, .35, .8],
      [.6, .75, .375, .81],
      [.5, .8, .4, .82],
      [.4, .85, .425, .83],
      [.3, .9, .45, .85],
      [.2, .95, .475, .9],
      [.1, 1, .5, 1],
      [0, .9, .525, 1]]

el = [[0, 0, 0, 0, 0],
      [1, 0, 0, 0, 0],
      [1, 1, 0, 0, 0],
      [1, 1, 0, 0, 0],
      [1, 1, 0, 0, 0],
      [1, 1, 1, 0, 0],
      [1, 1, 1, 0, 0],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1]]

qil = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1, 1, .95, .9, .9, .875, .85, .825, .8, .775]

qol = [1, .95, .9, .85, .8, .75, .7, .65, .6, .55, .5, .45, .4, .35, .3, .25, .2, .15, .1, .05, 0]



# fig, ax = plt.subplots()
#
# for j in range(3):
#     for i in range(s):
#         ax.clear()
#         visualize(4, 5, qil[i], qol[i], cl[i], el[i])
#         ax.set_title(f"frame {i}")
#         # Note that using time.sleep does *not* work here!
#         plt.pause(0.1)





from itertools import count
import random

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt


def animate(i, x=[], y=[]):
    ax.clear()
    x.append(i)
    y.append(random.randint(0, 10))

    visualize(4, 5, qil[i], qol[i], cl[i], el[i])


fig, ax = plt.subplots()
ani = FuncAnimation(fig, animate, interval=100, frames=20)
ani.save('animation.gif', writer='imagemagick', fps=10)
plt.show()