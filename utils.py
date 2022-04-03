import collections
import logging
import re
import socket

logger = logging.getLogger(__name__)

RE_IP = re.compile('(?P<prefix_host>^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.)(?P<last_ip>\\d{1,3}$)')


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


def find_neighbours(my_host, my_port, start_ip_range, end_ip_range, start_port, end_port):
    """他のブロックチェーンノードを見つける(5001,5002,5003)"""
    address = f'{my_host}:{my_port}'
    m = RE_IP.search(my_host)
    if not m:
        return None

    prefix_host = m.group('prefix_host')
    last_ip = m.group('last_ip')

    neighbours = []
    for ip_range in range(start_ip_range, end_ip_range):
        for guess_port in range(start_port, end_port):
            guess_host = f'{prefix_host}{int(last_ip) + int(ip_range)}'
            guess_address = f'{guess_host}:{guess_port}'
            if is_found_host(guess_host, guess_port) and not guess_address == address:
                neighbours.append(guess_address)
    return neighbours


def is_found_host(target, port):
    """他のブロックチェーンノードが起動しているか判定する"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        try:
            sock.connect((target, port))
            return True
        except Exception as ex:
            logger.debug({
                'action': 'is_found_host',
                'target': target,
                'port': port,
                'exception': ex
            })
            return False


def get_host():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as ex:
        logger.error({
            'action': 'get_host',
            'exception': ex
        })
        return '127.0.0.1'


if __name__ == '__main__':
    # print(is_found_host('127.0.0.1', 5010))
    print(find_neighbours(get_host(), 5009, 0, 3, 5001, 5004))
