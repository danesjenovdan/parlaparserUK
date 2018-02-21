# -*- coding: utf-8 -*-
import scrapy

class PeopleSpider(scrapy.Spider):
    name = 'people'

    start_urls = [
        'http://www.publicwhip.org.uk/mps.php',
        ]

    def parse(self, response):
        print('parser MPs', response)
        for i, mp in enumerate(response.css('table.mps > tr')):
            if i == 0:
                print('continue')
                continue
            # dont parse too much
            #if i ==12:
            #    break
            line = get_row_text(mp.css('td'))
            yield {'type': 'mp', 'name': line[0], 'distict': line[1] , 'party': line[2]}


def get_row_text(row):
    out = []
    for td in row:
        out.append(' '.join(t.strip() for t in td.css('::text').extract()).strip())
    return out
