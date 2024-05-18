#! /usr/bin/python3

from os import system


def enable_puppet() -> None:
    system('sudo puppet agent --enable')
    system('sudo puppet agent -tv')
    system('logsalmsg enabled puppet')


if __name__ == '__main__':
    enable_puppet()
