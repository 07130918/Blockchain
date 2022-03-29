import collections


def sorted_dict_by_key(unsorted_dict):
    """ キーの順番が異なって入って来ても同じハッシュを生成するために、ソートされるようにする """
    return collections.OrderedDict(sorted(unsorted_dict.items(), key=lambda d: d[0]))


def pprint(chains):
    for i, chain in enumerate(chains):
        print(f'{"="*25} Chain {i} {"="*25}')
        for k, v in chain.items():
            if k == 'transactions':
                print(f'{k}:')
                for d in v:
                    for kk, vv in d.items():
                        print(f'{" ":15}{kk:30}{vv}')
            else:
                print(f'{k:15}{v}')
