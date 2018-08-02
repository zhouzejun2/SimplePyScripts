#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from multiprocessing import Process, Lock
import time


def f(lock, i):
    with lock:
        print('hello world', i)

        time.sleep(1)


if __name__ == '__main__':
    lock = Lock()

    for num in range(10):
        Process(target=f, args=(lock, num)).start()
