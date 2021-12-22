"""Obelisk extract historical data to CSV."""

__author__ = 'Pieter Moens'
__email__ = 'Pieter.Moens@UGent.be'

import csv
import pathlib

from obelisk.consumer import ObeliskConsumer
from example.config import ObeliskConfig

if __name__ == '__main__':
    c = ObeliskConsumer(ObeliskConfig.CLIENT_ID, ObeliskConfig.CLIENT_SECRET)

    scope = 'smm.demos.replay'
    outPath = pathlib.Path(f'./out/{scope}/')
    outPath.mkdir(parents=True, exist_ok=True)

    metrics = []
    has_next_page = True
    cursor = None
    while has_next_page:
        r = c.get_metrics(scope, cursor=cursor)
        for m in r.get('data'):
            metrics.append(m.get('id'))

        has_next_page = r.get('pagination').get('hasNextPage')
        cursor = r.get('pagination').get('nextCursor')

    for metric in ['event.test::json']:
        has_next_page = True
        write_headers = True
        while has_next_page:
            r = c.events(scope, metric, cursor=cursor, from_timestamp=1574640060000, to_timestamp=1574726340000)

            data = r.get('data')
            with open(outPath.joinpath(f'{metric}.csv'), 'a+', newline='') as mf:
                csv_writer = csv.writer(mf, delimiter=',')

                if write_headers:
                    csv_writer.writerow(data.get('columns'))
                    write_headers = False

                for event in data.get('values'):
                    csv_writer.writerow(event)

            has_next_page = r.get('pagination').get('hasNextPage')
            cursor = r.get('pagination').get('nextCursor')
