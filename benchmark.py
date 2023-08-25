from hierarchy_endpoint import Controller
import time
import matplotlib.pyplot as plt

NUM_SIM = 100
NUM_ITER = 100
PALLETS = {
    '001': [2, 0, "pen1"],
    '002': [3, 0, "pen2"],
    '003': [3, 1, "KUKA"],
    '004': [2, 1, "ABB1"],
    '005': [14, 0, "OMRON1"],
    '006': [15, 0, "pen3"],
    '007': [15, 1, "pen4"],
    '008': [14, 1, "UR"],
    '009': [25, 0, "ABB2"],
    '010': [26, 0, "OMRON2"],
    '011': [27, 0, "pen1"],
    '012': [27, 1, "pen2"],
    '013': [26, 1, "KUKA"],
    '014': [25, 1, "ABB1"],
    '015': [37, 0, "OMRON1"],
    '016': [38, 0, "pen3"],
    '017': [39, 0, "pen4"],
    '018': [39, 1, "UR"],
    '019': [38, 1, "ABB2"],
    '020': [37, 1, "OMRON2"],
    '021': [49, 0, "pen1"],
    '022': [50, 0, "pen2"],
    '023': [51, 0, "pen3"],
    '024': [51, 1, "pen4"],
    '025': [50, 1, "ABB2"],
    '026': [49, 1, "OMRON2"],
    '027': [1, 7, "pen1"],
    '028': [0, 7, "pen2"],
    '029': [0, 6, "KUKA"],
    '030': [1, 6, "ABB1"],
    '031': [13, 7, "OMRON1"],
    '032': [12, 7, "pen3"],
    '033': [12, 6, "pen4"],
    '034': [13, 6, "UR"],
    '035': [26, 7, "ABB2"],
    '036': [25, 7, "OMRON2"],
    '037': [24, 7, "pen1"],
    '038': [24, 6, "pen2"],
    '039': [25, 6, "pen3"],
    '040': [26, 6, "pen4"],
    '041': [38, 7, "ABB2"],
    '042': [37, 7, "OMRON2"],
    '043': [36, 7, "pen1"],
    '044': [36, 6, "pen2"],
    '045': [37, 6, "KUKA"],
    '046': [38, 6, "ABB1"],
    '047': [50, 7, "OMRON1"],
    '048': [49, 7, "pen3"],
    '049': [48, 7, "pen4"],
    '050': [48, 6, "UR"],
    '051': [49, 6, "ABB2"],
    '052': [50, 6, "OMRON2"],
        '101': [52, 2, "pen1"],
        '102': [53, 2, "pen2"],
        '103': [54, 2, "KUKA"],
        '104': [55, 2, "ABB1"],
        '105': [56, 2, "OMRON1"],
        '106': [57, 2, "pen3"],
        '107': [52, 3, "pen4"],
        '108': [53, 3, "UR"],
        '109': [54, 3, "ABB2"],
        '110': [55, 3, "OMRON2"],
        '111': [56, 3, "pen1"],
        '112': [57, 3, "pen2"],
        '113': [52, 4, "KUKA"],
        '114': [53, 4, "ABB1"],
        '115': [54, 4, "OMRON1"],
        '116': [55, 4, "pen3"],
        '117': [56, 4, "pen4"],
        '118': [57, 4, "UR"],
        '119': [52, 5, "ABB2"],
        '120': [53, 5, "OMRON2"],
        '121': [54, 5, "pen1"],
        '122': [55, 5, "pen2"],
        '123': [56, 5, "pen3"],
        '124': [57, 5, "pen4"],
    #     '025': [0, 2, "ABB2"],
    #     '026': [1, 2, "OMRON2"],
    #     '027': [2, 2, "pen1"],
    #     '028': [3, 2, "pen2"],
    #     '029': [0, 3, "KUKA"],
    #     '030': [1, 3, "ABB1"],
    #     '031': [2, 3, "OMRON1"],
    #     '032': [3, 3, "pen3"],
    #     '033': [0, 4, "pen4"],
    #     '034': [1, 4, "UR"],
    #     '035': [2, 4, "ABB2"],
    #     '036': [3, 4, "OMRON2"],
    #     '037': [0, 5, "pen1"],
    #     '038': [1, 5, "pen2"],
    #     '039': [2, 5, "pen3"],
    #     '040': [3, 5, "pen4"],
}


def init_scene(controller):
    for pallet_id, pallet in PALLETS.items():
        x, y = pallet[0], pallet[1]
        if x is not None and y is not None:
            controller.add_pallet(x, y)
        else:
            controller.add_pallet()


def run(controller):
    for _ in range(NUM_ITER):
        controller.update()


def dl_analysis(history):
    data = []
    for path in history:
        arr = []
        i = 1
        delay = 0
        while i < len(path):
            if path[i - 1] == path[i]:
                delay += 1
            elif delay > 0:
                arr.append(delay)
                delay = 0
            i += 1
        if len(arr) > 0:
            data.append(arr)

    max_delay = max([max(arr) for arr in data])
    total_delay = sum([sum(arr) for arr in data])
    robots = len(data)
    avg_delay = sum([sum(arr) / len(arr) for arr in data]) / robots
    return max_delay, total_delay, avg_delay, robots


if __name__ == '__main__':
    result = []
    dl_summary = []
    roadmap = 'hex_roadmap3.json'
    topology = 'hex_topology3.json'
    windows = 1
    gain = 10
    for i in range(NUM_SIM):
        cont = Controller(H=windows, K=gain, roadmap=roadmap, topology=topology)
        init_scene(cont)
        st = time.time()
        run(cont)
        et = time.time()
        result.append(et - st)
        hist = cont.get_history()
        max_delay, total_delay, avg_delay, robots = dl_analysis(hist)
        dl_summary.append([max_delay, total_delay, avg_delay, robots])
        del cont
        print(f"Round {i + 1}th ended: {et - st:.3f}s, average delay: {avg_delay:.3f}")

    summary = f'Number of simulations: {NUM_SIM} \n' \
              f'Number of iterations: {NUM_ITER} \n' \
              f'Number of pallets: {len(PALLETS)} \n' \
              f'Parameters: H = {windows}, K = {gain} \n' \
              f'Maximum computation time: {max(result):.3f} / {NUM_ITER} ({max(result) / NUM_ITER:.3f})\n' \
              f'Minimum computation time: {min(result):.3f} / {NUM_ITER} ({min(result) / NUM_ITER:.3f})\n' \
              f'Average computation time: {sum(result) / NUM_SIM:.3f} / {NUM_ITER} ({sum(result) / NUM_SIM / NUM_ITER:.3f})\n' \
              f'Mean computation time: {sorted(result)[len(result) // 2]:.3f} \n' \
              f'Maximum delay on a pallet: {max([dl[0] for dl in dl_summary])} \n' \
              f'Average delay for each pallet: {sum([dl[2] for dl in dl_summary]) / NUM_SIM:.3f} \n' \
              f'Average total delay of each simulation: {sum([dl[1] for dl in dl_summary]) // NUM_SIM}\n' \
              f'Average number of robots delayed: {sum([dl[3] for dl in dl_summary]) // NUM_SIM}\n' \
              f'Files used: {roadmap}, {topology} \n'

    print(f'Finished!\n{summary}')

    with open("benchmarking.txt", 'a') as f:
        f.write(f"\n{summary}Data: \n{result}\n")

    plt.hist(result, bins=int(max(result) - min(result)))
    plt.ylabel('% run ended')
    plt.xlabel('Time (s)')
    plt.show()
