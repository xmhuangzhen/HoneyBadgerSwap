import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from ratel.benchmark.src import trade_throughput, trade_latency

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


if __name__ == '__main__':
    pool_num_list = [1, 2, 4, 8, 16]
    players = 4
    clients = 10
    prog = 'hbswap'

    throughput_list = []
    for pool_num in pool_num_list:
        throughput = 0
        for server_id in range(players):
            dir = f'ratel/benchmark/data/{players}_{clients if pool_num < clients else 2 * clients}_{pool_num}_{2 * pool_num}'
            _, _, _, _, _, mean = trade_throughput.scan(dir, prog, server_id)
            throughput += mean
        throughput /= players
        throughput_list.append(throughput)
    print(throughput_list)

    latency_list = []
    for pool_num in pool_num_list:
        latency = 0
        for server_id in range(players):
            dir = f'ratel/benchmark/data/{players}_{clients if pool_num < clients else 2 * clients}_{pool_num}_{2 * pool_num}'
            mean, _, _ = trade_latency.scan(dir, prog, server_id)
            latency += mean
        latency /= players
        latency_list.append(latency)
    print(latency_list)

    colors = list(mcolors.TABLEAU_COLORS.keys())

    fig = plt.figure()
    ax1 = fig.add_subplot()
    ax2 = ax1.twinx()

    ax1.plot(pool_num_list, latency_list, color='teal', marker='v', label=f'latency')
    ax2.plot(pool_num_list, throughput_list, color='crimson', marker='o', label=f'throughput')

    ax1.set_xlabel('Trading pool number')
    ax1.set_ylabel('Average trades latency(s)')
    ax2.set_ylabel('Average trades throughput(/min)')
    ax1.set_xlim(0, 17)
    ax1.set_ylim(0, 8)
    ax2.set_ylim(0, 180)
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax1.set_xticks(np.arange(0, 17, step=2))
    # plt.show()
    plt.subplots_adjust(left=0.08, bottom=0.13, right=0.88, top=0.95, wspace=0, hspace=0)
    save_file = f'ratel/benchmark/data/concurrent.pdf'
    plt.savefig(save_file)
