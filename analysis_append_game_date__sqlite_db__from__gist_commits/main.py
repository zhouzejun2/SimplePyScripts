#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# Parser from https://github.com/gil9red/played_games/blob/master/mini_played_games_parser.py
def parse_played_games(text: str, silence: bool=False) -> dict:
    """
    Функция для парсинга списка игр.

    """

    FINISHED_GAME = 'FINISHED_GAME'
    NOT_FINISHED_GAME = 'NOT_FINISHED_GAME'
    FINISHED_WATCHED = 'FINISHED_WATCHED'
    NOT_FINISHED_WATCHED = 'NOT_FINISHED_WATCHED'

    FLAG_BY_CATEGORY = {
        '  ': FINISHED_GAME,
        '- ': NOT_FINISHED_GAME,
        ' -': NOT_FINISHED_GAME,
        ' @': FINISHED_WATCHED,
        '@ ': FINISHED_WATCHED,
        '-@': NOT_FINISHED_WATCHED,
        '@-': NOT_FINISHED_WATCHED,
    }

    # Регулярка вытаскивает выражения вида: 1, 2, 3 или 1-3, или римские цифры: III, IV
    import re
    PARSE_GAME_NAME_PATTERN = re.compile(r'(\d+(, *?\d+)+)|(\d+ *?- *?\d+)|([MDCLXVI]+(, ?[MDCLXVI]+)+)',
                                         flags=re.IGNORECASE)

    def parse_game_name(game_name: str) -> list:
        """
        Функция принимает название игры и пытается разобрать его, после возвращает список названий.
        У некоторых игр в названии может указываться ее части или диапазон частей, поэтому для правильного
        составления списка игр такие случаи нужно обрабатывать.

        Пример:
            "Resident Evil 4, 5, 6" -> ["Resident Evil 4", "Resident Evil 5", "Resident Evil 6"]
            "Resident Evil 1-3"     -> ["Resident Evil", "Resident Evil 2", "Resident Evil 3"]
            "Resident Evil 4"       -> ["Resident Evil 4"]

        """

        match = PARSE_GAME_NAME_PATTERN.search(game_name)
        if match is None:
            return [game_name]

        seq_str = match.group(0)

        # "Resident Evil 4, 5, 6" -> "Resident Evil"
        # For not valid "Trollface Quest 1-7-8" -> "Trollface Quest"
        index = game_name.index(seq_str)
        base_name = game_name[:index].strip()

        seq_str = seq_str.replace(' ', '')

        if ',' in seq_str:
            # '1,2,3' -> ['1', '2', '3']
            seq = seq_str.split(',')

        elif '-' in seq_str:
            seq = seq_str.split('-')

            # ['1', '7'] -> [1, 7]
            seq = list(map(int, seq))

            # [1, 7] -> ['1', '2', '3', '4', '5', '6', '7']
            seq = list(map(str, range(seq[0], seq[1] + 1)))

        else:
            return [game_name]

        # Сразу проверяем номер игры в серии и если она первая, то не добавляем в названии ее номер
        return [base_name if num == '1' else base_name + " " + num for num in seq]

    from collections import OrderedDict
    platforms = OrderedDict()
    platform = None

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue

        if line[0] not in ' -@' and line[1] not in ' -@' and line.endswith(':'):
            platform_name = line[:-1]

            platform = OrderedDict()
            platform[FINISHED_GAME] = list()
            platform[NOT_FINISHED_GAME] = list()
            platform[FINISHED_WATCHED] = list()
            platform[NOT_FINISHED_WATCHED] = list()

            platforms[platform_name] = platform

            continue

        if not platform:
            continue

        flag = line[:2]
        category_name = FLAG_BY_CATEGORY.get(flag)
        if not category_name:
            if not silence:
                print('Странный формат строки: "{}"'.format(line))

            continue

        category = platform[category_name]

        game_name = line[2:]
        for game in parse_game_name(game_name):
            if game in category:
                if not silence:
                    print('Предотвращено добавление дубликата игры "{}"'.format(game))

                continue

            category.append(game)

    return platforms


# Get FULL database from: https://github.com/gil9red/SimplePyScripts/blob/2f50908d5c70fafa885db009bfe9570f8fc111e8/PyGithub_examples/gist_history_to_sqlite_db.py
DB_FILE_NAME = 'gist_commits.sqlite'


def create_connect():
    import sqlite3
    return sqlite3.connect(DB_FILE_NAME)


if __name__ == '__main__':
    from collections import defaultdict
    append_game_date = defaultdict(dict)

    FINISHED_GAME = 'FINISHED_GAME'
    FINISHED_WATCHED = 'FINISHED_WATCHED'

    with create_connect() as connect:
        for committed_at, content in connect.execute('SELECT committed_at, content FROM GistFile'):
            platforms = parse_played_games(content, silence=True)
            for platform, categories in platforms.items():
                if platform not in append_game_date:
                    append_game_date[platform] = defaultdict(dict)

                for game in categories[FINISHED_GAME]:
                    if game not in append_game_date[platform][FINISHED_GAME]:
                        append_game_date[platform][FINISHED_GAME][game] = committed_at

                for game in categories[FINISHED_WATCHED]:
                    if game not in append_game_date[platform][FINISHED_WATCHED]:
                        append_game_date[platform][FINISHED_WATCHED][game] = committed_at

    # Check
    print('Ведьмак:', append_game_date['PC']['FINISHED_GAME']['Ведьмак'])
    print('Dragon Age II:', append_game_date['PC']['FINISHED_GAME']['Dragon Age II'])
