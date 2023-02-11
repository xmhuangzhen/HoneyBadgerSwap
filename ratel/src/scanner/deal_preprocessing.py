import os
import re
import sys

from ratel.src.python.utils import BUFFER_SIZE

if __name__ == "__main__":
    app = sys.argv[1]

    dir = './ratel/mpc_out'
    for filename in os.listdir(dir):
        mpc_prog_name = filename[:-4]
        sol_out_file_list = re.split(f'{app}|\d+', mpc_prog_name)
        if len(sol_out_file_list) == 3:
            func_name = sol_out_file_list[1]

            with open(f'{dir}/{filename}', 'r') as f:
                sol_out = ''
                for line in f.readlines():
                    element = line.split()
                    if element[1] == 'integer':
                        num = ((int(element[0]) - 1) // BUFFER_SIZE + 1) * BUFFER_SIZE
                        element_type = element[2][:-1].upper()
                        sol_out += f'\t\t' \
                                   f'require(numTotalPreprocessedElement[uint8(PreprocessedElementType.{element_type})]' \
                                   f' - numUsedPreprocessedElement[uint8(PreprocessedElementType.{element_type})]' \
                                   f' >= {num}, \"Shortage of available {element[2]}. Retry later!\");\n'
                        sol_out += f'\t\tinitIndex{element_type}[seq{func_name}][\"{mpc_prog_name}\"] ' \
                                   f'= numUsedPreprocessedElement[uint8(PreprocessedElementType.{element_type})];\n'
                        sol_out += f'\t\tnumUsedPreprocessedElement[uint8(PreprocessedElementType.{element_type})] +=' \
                                   f' {num};\n'

            with open(f'{dir}/{func_name}.sol', 'a') as f:
                f.write(sol_out)
