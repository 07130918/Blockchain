import collections


def sorted_dict_by_key(unsorted_dict):
    """ キーの順番が異なって入って来ても同じハッシュを生成するために、ソートされるようにする """
    return collections.OrderedDict(sorted(unsorted_dict.items(), key=lambda d: d[0]))
