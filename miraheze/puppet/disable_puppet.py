#! /usr/bin/python3

from os import system
import sys


def disable_puppet() -> None:
    system(f'logsalmsg Disabling puppet for {sys.argv[1]}')
    system('sudo puppet agent -tv')
    system(f'sudo puppet agent --disable "{sys.argv[1]}"')


if __name__ == '__main__':
    disable_puppet()
