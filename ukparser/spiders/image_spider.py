# -*- coding: utf-8 -*-
import scrapy

class PeopleSpider(scrapy.Spider):
    name = 'images'

    custom_settings = {
        'ITEM_PIPELINES': {
            'ukparser.pipelines.ImagesPipeline': 1
        }
    }

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
            img_url =  'http://www.publicwhip.org.uk/' + mp.css('td > a::attr(href)').extract()[0]
            yield scrapy.Request(url=img_url, callback=self.parse_twfy_url)

    def parse_twfy_url(self, response):
        twfy_url = response.css("div#main ul a::attr(href)").extract()[0]
        yield scrapy.Request(url=twfy_url, callback=self.parse_image)

    def parse_image(self, response):
        img_url = 'https://www.theyworkforyou.com' + response.css("div.mp-image > img::attr(src)").extract()[0]
        name = response.css("div.mp-name-and-position > h1::text").extract()[0]
        yield {'image_urls': [img_url], 'name': name}
