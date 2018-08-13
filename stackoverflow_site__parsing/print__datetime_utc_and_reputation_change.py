#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import requests
from bs4 import BeautifulSoup
import datetime as DT


def get_day_by_rep(url: str) -> dict:
    rs = requests.get(url)
    root = BeautifulSoup(rs.content, 'html.parser')

    day_by_rep = dict()

    for row in root.select('.rep-table-row'):
        day = row.select_one('.rep-day')['title']
        rep = row.select_one('.rep-cell').text.strip()

        day = DT.datetime.strptime(day, '%Y-%m-%d')

        day_by_rep[day] = rep

    return day_by_rep


if __name__ == '__main__':
    url = 'https://ru.stackoverflow.com/users/201445/gil9red?tab=reputation'
    day_by_rep = get_day_by_rep(url)

    start_date, end_date = min(day_by_rep), max(day_by_rep)
    print('Start: {}, end: {}'.format(start_date, end_date))
    print()

    # Print
    for day, rep in sorted(day_by_rep.items(), key=lambda x: x[0]):
        print('{:%d/%m/%Y} : {}'.format(day, rep))