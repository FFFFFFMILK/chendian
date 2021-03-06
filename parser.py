#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
import os
import re
import sys

__version__ = '0.1.1'
encoding = sys.stdout.encoding
logger = logging.getLogger(__name__)


class Message(object):
    def __init__(self, text, msg_handlers):
        self.text = text
        self.r_msg = re.compile(ur"""
            (?<=\n)
            (\d{4}\-\d{1,2}\-\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,3})  # date
            \s+
            (.*?)                                                # nickname
            (?:\((\d+)\)|<([^>]+)>)\n                            # QQ number
            (.*?)                                                # message
            (?=(?:\d{4}-\d{1,2}-\d{1,2})|\n+$)
        """, re.I | re.X | re.S)
        self.msg_handlers = []
        self.msg_handlers.extend(msg_handlers)

    def _parse(self):
        for data in self.r_msg.findall(self.text):
            date_str, nickname, qq, email, msg = data
            qq = qq or email
            try:
                yield {
                    'date': datetime.datetime.strptime(
                        date_str,
                        '%Y-%m-%d %H:%M:%S'
                    ),
                    'nickname': nickname.strip(),
                    'qq': qq.strip(),
                    'msg': msg.strip(),
                }
            except Exception as e:
                logger.exception(e)

    def _handle(self, msg):
        for handler in self.msg_handlers:
            handler(msg)

    def __call__(self):
        for msg in self._parse():
            self._handle(msg)


def main(file_name):
    from collections import defaultdict
    from io import open

    from prettytable import (
        # ALL,
        # FRAME, NONE,
        PrettyTable
    )
    import tablib

    week_num = 1
    try:
        with open('a.txt') as f:
            week_num = int(f.read().strip())
    except Exception as e:
        logger.exception(e)
    
    check = defaultdict(lambda: defaultdict(list))
    today = datetime.datetime.today().date()
    datas = [today + datetime.timedelta(days=i)
             for i in range(0 - (7 * (week_num - 1)) - today.weekday(),
                             7 - today.weekday())
             ]
    
    def handler(msg):
        if msg['date'].date() in datas:
            if re.match(ur'\s*打卡', msg['msg']):
                check[msg['qq']][msg['date'].date()].append(msg)

    with open(file_name, encoding='utf-8-sig') as f:
        Message(f.read().replace('\r\n', '\n'), [handler])()

    
    table = PrettyTable([' Name'] + [u'%s' % (x.strftime('%m-%d(%a)')) for x in datas])
    headers_csv = [u' Name'] + [x.strftime('%Y-%m-%d\n(%A)') for x in datas]
    data_csv = []

    for v in check.values():
        name = u'%s(%s)' % (v.values()[-1][-1]['nickname'], v.values()[-1][-1]['qq'])
        row_csv = [name]
        row = [name[:15]]

        for d in datas:
            item = v[d]
            if item:
                # row.append(u'✔')
                row.append(u'OK')
                row_csv.append(u'\n'.join([x[u'msg'] + '\n' for x in item]))
            else:
                # row.append(u'✘')
                row.append(u' ')
                row_csv.append(u'')
        table.add_row(row)
        data_csv.append(row_csv)

    # table.hrules = NONE
    # table.hrules = FRAME
    # table.hrules = ALL
    table.align = 'c'
    table.align[' Name'] = 'l'
    table.valign = 'm'
    table.valign[' Name'] = 'm'
    table.padding_width = 1
    # table.left_padding_width = 0
    # table.right_padding_width = 0
    print(table.get_string().encode(encoding, 'replace'))
    with open('checkin_%s.xls' % today.strftime('%m-%d'), 'wb') as f:
        f.write(tablib.Dataset(*data_csv, headers=headers_csv
                               ).xls
                )

    raw_input('Finished! ')


if __name__ == '__main__':
    format_str = ('%(asctime)s - %(name)s'
                  ' - %(funcName)s - %(lineno)d - %(levelname)s'
                  ' - %(message)s')
    logging.basicConfig(filename='debug.log', level=logging.DEBUG,
                        format=format_str)
    try:
        file_name = 'data.txt'
        if not os.path.exists(file_name):
            raw_input(u'缺少 data.txt 文件'.encode(encoding))
            sys.exit(1)
        else:
            main('data.txt')
    except Exception as e:
        logger.exception(e)