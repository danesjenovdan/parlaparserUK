# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime


class ContentSpider(scrapy.Spider):
    name = "content"
    custom_settings = {
        'ITEM_PIPELINES': {
            'ukparser.pipelines.UkparserPipeline': 300,
        }
    }
    count = 0


    start_urls = [
        'http://www.publicwhip.org.uk/divisions.php',
        ]

    def parse(self, response):
        #print('parser vote urls', response)
        for i, vote in enumerate(response.css('table.votes > tr')):
            if i == 0:
                print("continue")
                continue
            # dont parse too much
            #if i ==2:
            #    break
            self.count += 1
            print("Count: ", self.count)
            if vote.css("td::text").extract()[0] == 'Commons':
                url = 'http://www.publicwhip.org.uk/' + vote.css("td > a::attr(href)").extract()[0]
                yield scrapy.Request(url=url, callback=self.get_balots_url)
        print('nc nisem yieldu')


    def get_balots_url(self, response):
        parse_motion = True
        # DEBATES
        text = ''
        fdate = None
        try:
            mot_id = response.url.split('number=')[1]
        except:
            mot_id = ''

        print("MOTION ID FROM URL", mot_id)

        if parse_motion:
            parse_motion = False
            title = response.css('div#main > h1::text').extract()[0]
            date = title.split(' — ')[-1]
            while not date[0].isdigit():
                date = date[1:]
            if 'at' in date.strip():
                fdate = datetime.strptime(date.strip(), '%d %b %Y at %H:%M')
            else:
                fdate = datetime.strptime(date.strip(), '%d %b %Y')
            text = ' — '.join(title.split(' — ')[:-1]).strip()

            text += '||' + mot_id
            yield {'type': 'debate',
                   'date': fdate,
                   'text': text.strip(),
                   'motion_note': get_row_text(response.css('div.motion'))[0]}
        # BALLOTS

        for paragraf in response.css('div#main > p'):
            print("ballot")
            for href in paragraf.css('a'):
                if href.css('::text').extract()[0] == 'all votes':
                    url = 'http://www.publicwhip.org.uk/' + href.css('::attr(href)').extract()[0]
                    request = scrapy.Request(url=url, callback=self.parse_ballots)
                    request.meta['text'] = text
                    yield request


        # SPEECHES
        url = response.css('div#main > div.motion > p > b').css("a::attr(href)").extract()[0]
        request = scrapy.Request(url=url, callback=self.parse_speeches)
        request.meta['text'] = text
        request.meta['fdate'] = fdate
        yield request


    def parse_ballots(self, response):
        title = response.css('div#main > h1::text').extract()[0]
        date = title.split(' — ')[-1]
        try:
            fdate = datetime.strptime(date.strip(), '%d %b %Y at %H:%M')
        except:
            fdate = datetime.strptime(date.strip(), '%d %b %Y')

        #text = ' — '.join(title.split(' — ')[:-1])
        text = response.meta['text']
        ballots = []
        for i, ballot in enumerate(response.css('table.votes > tr')):
            if i == 0:
                print("continue")
                continue
            tds = get_row_text(ballot.css('td'))
            name = tds[0]
            option = tds[3]
            party = tds[2]

            ballots.append(
                {
                    'voter': name,
                    'option': option,
                    'party': party,
                }
            )
        data = {
            'type': 'ballots',
            'date': fdate,
            'text' : text.strip(),
            'ballots': ballots
        }
        yield data

    def parse_speeches(self, response):
        speech_order = 0
        nums = ["th", "rd", "nd", "st"]
        text = response.meta['text']
        ddate = response.meta['fdate']

        speeches = []
        for speech in response.css('div.debate-speech'):
            try:
                speaker = speech.css('strong.debate-speech__speaker__name::text').extract()[0]
                speech_order += 1
            except:
                continue
            #date = ' '.join(speech.css("a.time::text").extract()[0].strip().split()).replace('\n', '')
            #for num in nums:
            #    if num in date:
            #        date = date.replace(num, '')
            #fdata = datetime.strptime(date.strip(), '%H:%M %p, %d %B %Y')
            content = get_row_text(speech.css('div.debate-speech__content'))[0]

            speeches.append({
               'speaker': speaker,
               'content': content,
               'date': ddate, 
               'order': speech_order
            })
        yield {
            'type': 'speech',
            'date': ddate,
            'debate_text': text,
            'debate_date': ddate,
            'speeches': speeches
        }


def get_row_text(row):
    out = []
    for td in row:
        out.append(' '.join(t.strip() for t in td.css('::text').extract()).strip())
    return out

