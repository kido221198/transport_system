from hierarchy_endpoint import Controller
import time
import matplotlib.pyplot as plt

NUM_SIM = 200
NUM_ITER = 100
PALLETS = {
    '001': [2, 0],
    '002': [3, 0],
    '003': [4, 0],
    '004': [5, 0],
    '005': [5, 1],
    '006': [4, 1],
    '007': [3, 1],
    '008': [2, 1],
    '009': [14, 0],
    '010': [15, 0],
    '011': [16, 0],
    '012': [17, 0],
    '013': [17, 1],
    '014': [16, 1],
    '015': [15, 1],
    '016': [14, 1],
    '017': [26, 0],
    '018': [27, 0],
    '019': [28, 0],
    '020': [29, 0],
    '021': [29, 1],
    '022': [28, 1],
    '023': [27, 1],
    '024': [26, 1],
    '025': [38, 0],
    '026': [39, 0],
    '027': [40, 0],
    '028': [41, 0],
    '029': [41, 1],
    '030': [40, 1],
    '031': [39, 1],
    '032': [38, 1],
    '033': [50, 0],
    '034': [51, 0],
    '035': [52, 0],
    '036': [53, 0],
    '037': [53, 1],
    '038': [52, 1],
    '039': [51, 1],
    '040': [50, 1],
    '041': [3, 7],
    '042': [2, 7],
    '043': [1, 7],
    '044': [0, 7],
    '045': [0, 6],
    '046': [1, 6],
    '047': [2, 6],
    '048': [3, 6],
    '049': [15, 7],
    '050': [14, 7],
    '051': [13, 7],
    '052': [12, 7],
    '053': [12, 6],
    '054': [13, 6],
    '055': [14, 6],
    '056': [15, 6],
    '057': [27, 7],
    '058': [26, 7],
    '059': [25, 7],
    '060': [24, 7],
    '061': [24, 6],
    '062': [25, 6],
    '063': [26, 6],
    '064': [27, 6],
    '065': [39, 7],
    '066': [38, 7],
    '067': [37, 7],
    '068': [36, 7],
    '069': [36, 6],
    '070': [37, 6],
    '071': [38, 6],
    '072': [39, 6],
    '073': [51, 7],
    '074': [50, 7],
    '075': [49, 7],
    '076': [48, 7],
    '077': [48, 6],
    '078': [49, 6],
    '079': [50, 6],
    '080': [51, 6],
}


def init_scene(controller, pallet_num):
    from random import sample
    # print(PALLETS.values(), type(PALLETS.values()))
    for pallet in sample(list(PALLETS.values()), pallet_num):
        x, y = pallet[0], pallet[1]
        if x is not None and y is not None:
            controller.add_pallet(x, y)
        else:
            controller.add_pallet()


def run(controller):
    data = {'occupied': [],
            'capacity': controller.get_capacity()}
    for _ in range(NUM_ITER):
        controller.update()
        data['occupied'].append(controller.get_occupied())
    return data


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

    max_delay = max([max(arr) for arr in data]) if len(data) > 0 else 0
    total_delay = sum([sum(arr) for arr in data]) if len(data) > 0 else 0
    robots = len(data)
    avg_delay = sum([sum(arr) / len(arr) for arr in data]) / robots if len(data) > 0 else 0
    return max_delay, total_delay, avg_delay, robots


def occupation_analysis(data):
    excluded = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62]
    cap, occ = list(data['capacity']), data['occupied']
    # print(dict(occ[0]))
    lst = sorted([round(dict(o)[i + 1] / cap[i][1] * 100, 3)
                  for o in occ for i in range(len(cap)) if i + 1 not in excluded])
    lst = [x for x in lst if x > 0]
    first_quart = lst[len(lst) // 4]
    mean = lst[len(lst) // 2]
    third_quart = lst[3 * len(lst) // 4]
    avg = round(sum(lst) / len(lst), 3)
    return first_quart, mean, third_quart, avg


if __name__ == '__main__':
    result = []
    dl_summary = []
    occ_summary = {'first_quart': [], 'mean': [], 'third_quart': [], 'avg': []}
    roadmap = 'hex_roadmap4.json'
    topology = 'hex_topology4.json'
    comment = 'Origin.'
    windows = 1
    gain = 10
    pallet_num = 80

    for i in range(NUM_SIM):
        cont = Controller(H=windows, K=gain, roadmap=roadmap, topology=topology, origin=True)
        init_scene(cont, pallet_num)
        st = time.time()
        occ_data = run(cont)
        et = time.time()
        result.append(et - st)
        hist = cont.get_history()
        max_delay, total_delay, avg_delay, robots = dl_analysis(hist)
        dl_summary.append([max_delay, total_delay, avg_delay, robots])
        first_quart, mean, third_quart, avg = occupation_analysis(occ_data)
        occ_summary['first_quart'].append(first_quart)
        occ_summary['mean'].append(mean)
        occ_summary['third_quart'].append(third_quart)
        occ_summary['avg'].append(avg)
        del cont
        print(f"Round {i + 1}th ended: {et - st:.3f}s, avg. delay: {avg_delay:.3f}, avg. occupation: {avg:.3f} \n"
              f"Preparing new round...", end='\r')

    summary = f'Number of simulations: {NUM_SIM} \n' \
              f'Number of iterations: {NUM_ITER} \n' \
              f'Number of pallets: {pallet_num} \n' \
              f'Parameters: H = {windows}, K = {gain} \n' \
              f'Maximum computation time: {max(result):.3f} / {NUM_ITER} ({max(result) / NUM_ITER:.3f})\n' \
              f'Minimum computation time: {min(result):.3f} / {NUM_ITER} ({min(result) / NUM_ITER:.3f})\n' \
              f'Average computation time: {sum(result) / NUM_SIM:.3f} / {NUM_ITER} ({sum(result) / NUM_SIM / NUM_ITER:.3f})\n' \
              f'Mean computation time: {sorted(result)[len(result) // 2]:.3f} \n' \
              f'Maximum delay on a pallet: {max([dl[0] for dl in dl_summary])} \n' \
              f'Average delay for each pallet: {sum([dl[2] for dl in dl_summary]) / NUM_SIM:.3f} \n' \
              f'Average total delay of each simulation: {sum([dl[1] for dl in dl_summary]) // NUM_SIM}\n' \
              f'Average number of robots delayed: {sum([dl[3] for dl in dl_summary]) // NUM_SIM}\n' \
              f'Average occupation: {sum(occ_summary["avg"]) / NUM_SIM:.3f}\n' \
              f'First quartile occupation: {sum(occ_summary["first_quart"]) / NUM_SIM:.3f}\n' \
              f'Mean occupation: {sum(occ_summary["mean"]) / NUM_SIM:.3f}\n' \
              f'Third quartile occupation: {sum(occ_summary["third_quart"]) / NUM_SIM:.3f}\n' \
              f'Files used: {roadmap}, {topology} \n' \
              f'{comment}\n'

    print(f'Finished!\n{summary}')

    with open("benchmarking.txt", 'a') as f:
        f.write(f"\n{summary}Data: \n{result}\n")

    plt.hist(result, bins=int(max(result) - min(result)))
    plt.ylabel('% run ended')
    plt.xlabel('Time (s)')
    plt.show()
