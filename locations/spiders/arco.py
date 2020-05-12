# -*- coding: utf-8 -*-
import csv
import re
import scrapy
import urllib

from locations.items import GeojsonPointItem


class ArcoSpider(scrapy.Spider):
    name = "arco"
    item_attributes = {'brand': "ARCO", 'brand_wikidata': "Q304769"}
    allowed_domains = ["www.arco.com"]
    download_delay = 0.2

    start_urls = ['https://www.arco.com/scripts/stationfinder.js']

    def parse(self, response):
        if response.url == self.start_urls[0]:
            match = re.search("var csv_url = '(.*)'",
                              response.body_as_unicode())
            assert match.group(1)

            yield scrapy.Request(f"https://www.arco.com{match.group(1)}")
        else:
            for station in csv.DictReader(response.body_as_unicode().splitlines()):
                yield GeojsonPointItem(
                    lat=station['Lat'],
                    lon=station['Lng'],
                    name=station['StoreName'],
                    addr_full=station['Address'],
                    city=station['City'],
                    state=station['State'],
                    postcode=station['Zip'],
                    country='US' if len(station['State']) == 2 else 'MX',
                    phone=station['Phone'],
                    ref=station['StoreNumber'],
                    extras={
                        'accepts_credit_cards': station['CreditCards'] == '1',
                        'convenience_store': station['ampm'] == '1'
                    }
                )
