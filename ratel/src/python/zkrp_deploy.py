import sys

from web3 import Web3
from web3.middleware import geth_poa_middleware
from ratel.src.python.utils import getAccount, parse_contract


if __name__=='__main__':
    appName = sys.argv[1]
    init_players = int(sys.argv[2])
    init_threshold = int(sys.argv[3])

    print('appName:',appName)
    print('initPlayers:',init_players)
