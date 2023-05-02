import itertools
import time
from multiprocessing import Pool, cpu_count
import json
import sys

scenario = sys.argv[1]
scenario_file = f'./scenarios/{scenario}.json'
with open(scenario_file, 'r') as f:
    DECK = json.load(f)

# Optimal pool count = number of logical cores on computer, subtract 1 not to brick computer :) 
CORES = cpu_count() - 1

INITIAL_CARD_TYPE_AMOUNTS = {card_type: deck_data['amount'] for card_type, deck_data in DECK.items()}


def generate_permutations():
    print('————————————————————————————————————————————————————————————————')
    start_time = time.time()
    probability_of_mulliganing = 1
    for i in range(0, 7):
        probability_of_mulliganing *= (60 - i - DECK['basic_pokemon']['amount']) / (60 - i)

    probability_of_not_mulliganing = 1 - probability_of_mulliganing

    card_types = list(DECK.keys())

    highest_within = max(sub_dict['within'] for key, sub_dict in DECK.items() if 'within' in sub_dict)

    print(f'Generating all {len(card_types) ** highest_within} permutations of cards...')


    # This can take some time - try to optimize?
    all_permutations = set(list(itertools.product(card_types, repeat=highest_within)))

    print(f'Generated {len(all_permutations)} permutations')
    print(f'Time elapsed: {time.time() - start_time:.4f} seconds')

    print('————————————————————————————————————————————————————————————————')
    return all_permutations, probability_of_not_mulliganing



PERMS = []
def filter_permutations(permutation):
    conditions = [
        (
            DECK[card_type].get('at_least', 0)
            <= sum(1 for card in permutation[:DECK[card_type]['within']] if card == card_type)
            <= DECK[card_type].get('at_most', DECK[card_type]['amount'])
        )
        for card_type in DECK if 'within' in DECK[card_type]
    ]
    if all(conditions):
        return permutation

    return None

def gen_probability(permutation):
    probability = 1
    card_type_amounts = INITIAL_CARD_TYPE_AMOUNTS.copy()
    for card in permutation:
        probability *= card_type_amounts[card] / sum(card_type_amounts.values())
        card_type_amounts[card] -= 1

    return probability

if __name__ == '__main__':
    print(f'Using scenario {scenario_file}')
    print(f'Using {CORES} cores...')
    start_time = time.time()

    filtered_permutations = []
    permutation_counter = 0
    time_counter = 1
    all_permutations, probability_of_not_mulliganing = generate_permutations()
    time_2 = time.time()

    with Pool(CORES) as p:
        filtered_permutations_bad = p.map(filter_permutations, all_permutations)# This can take some time - optimize?
        filtered_permutations = list(filter(lambda x: x is not None, filtered_permutations_bad))

    print(f'Permutations that meet the conditions: {len(filtered_permutations)}')
    print(f'Time elapsed: {time.time() - time_2:.4f} seconds')


    print('————————————————————————————————————————————————————————————————')
    time_3 = time.time()
    print('Adding probabilities...')

    cumulative_probability = 0
    permutation_counter = 0
    time_counter = 1
    with Pool(CORES) as p:
        probs = p.map(gen_probability, filtered_permutations)# This can take some time - optimize?
        cumulative_probability = sum(probs)

    print(f'Probability: {cumulative_probability * 100:.4f}%')
    print(f'Time elapsed: {time.time() - time_3:.4f} seconds')

    print('————————————————————————————————————————————————————————————————')
    print(f'Total time elapsed: {time.time() - start_time:.4f} seconds')
    print(f'Probability excluding mulligan hands: {cumulative_probability * 100 / probability_of_not_mulliganing:.4f}%')
    print("Cleaing up stuff...")