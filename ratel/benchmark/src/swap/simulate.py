### python3 -m ratel.benchmark.src.swap.simulate 86400 345600 traderjoev2_USDC.e_WAVAX

import re
import sys

import matplotlib.pyplot as plt
import numpy as np


# Set the default text font size
plt.rc('font', size=15)
# Set the axes title font size
plt.rc('axes', titlesize=15)
# Set the axes labels font size
plt.rc('axes', labelsize=15)
# Set the font size for x tick labels
plt.rc('xtick', labelsize=15)
# Set the font size for y tick labels
plt.rc('ytick', labelsize=15)
# Set the legend font size
plt.rc('legend', fontsize=12)
# Set the font size of the figure title
plt.rc('figure', titlesize=20)


interval = 5


def sample():
    return np.random.choice(list(pdf.keys()), p=list(pdf.values()))


def simulate():
    delay_dict = {}
    mpc_time = 0
    max_delay = 0
    cnt = 0
    with open(f'ratel/benchmark/src/swap/pool_data/{pool_name}.csv', 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:
            element = re.split(',|\t|\n', line)
            timestamp = float(element[0])

            if timestamp < start_time:
                continue
            if timestamp > end_time:
                break

            if mpc_time > timestamp:
                delay = mpc_time - timestamp
                mpc_time += sample()
            else:
                delay = 0
                mpc_time = timestamp + sample()

            if delay > max_delay:
                max_delay = delay

            if delay <= 60:
                cnt += 1

            key = (delay // interval) * interval
            # key = (delay // interval + 1) * interval
            if key not in delay_dict.keys():
                delay_dict[key] = 0
            delay_dict[key] += 1

    s = sum(delay_dict.values())

    delay_portion = {k: v / s for k, v in delay_dict.items()}

    return max_delay, cnt / s, delay_portion


if __name__ == '__main__':
    start_time = int(sys.argv[1])
    end_time = int(sys.argv[2])
    pool_name = sys.argv[3]

    with open(f'ratel/benchmark/src/swap/pdf.txt', 'r') as f:
        line = f.readlines()[0]
        pdf = eval(line)

    rep = 100
    lim = 180
    m = 0
    cnt = 0
    x = np.arange(0, lim, interval)
    values = np.zeros((rep, lim // interval))
    for i in range(rep):
        print('iteration', i)
        _m, _cnt, _values = simulate()
        m += _m
        cnt += _cnt
        for j, k in enumerate(x):
            if k in _values.keys():
                values[i][j] = _values[k]

    y = np.mean(values, axis=0)
    print(sum(y))

    for i in range(1, len(y)):
        y[i] += y[i - 1]
    err = np.std(values, axis=0)

    print(y)
    print(err)

    print('max delay', m / rep)
    print('percent less than 1min', cnt / rep)
    print('less than 5s', y[1])

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.set_xticks(x[::4])
    ax1.set_xlim(0, lim)
    ax1.set_ylim(0, 1)
    # ax1.bar(x + interval / 2, y, width=interval, color='cornflowerblue', yerr=err, ecolor='fuchsia')
    ax1.plot(x, y, color='cornflowerblue')
    ax1.set_xlabel('Wait time(s)')
    ax1.set_ylabel('Cumulative Distribution Function')
    plt.subplots_adjust(left=0.12, bottom=0.13, right=0.95, top=0.96, wspace=0, hspace=0)
    plt.savefig(f'ratel/benchmark/src/swap/sim.pdf')
