# -*- coding: utf-8 -*-
import scrapy
import json
import re
import traceback

from locations.items import GeojsonPointItem


class QuiznosSpider(scrapy.Spider):
    name = "quiznos"
    allowed_domains = ["restaurants.quiznos.com"]
    start_urls = (
        'http://restaurants.quiznos.com/data/stores.json?callback=storeList',
    )

    def parse(self, response):
        data = response.body_as_unicode()
        stores = json.loads(re.search('storeList\((.*)\)', data).group(1))

        for store in stores:

            yield GeojsonPointItem(
                lat=store.get('latitude'),
                lon=store.get('longitude'),
                ref=str(store.get('storeid')),
                phone=store.get('phone'),
                name=store.get('restaurantname'),
                opening_hours=store.get('businesshours'),
                addr_full=store.get('address1'),
                city=store.get('city'),
                state=store.get('statecode'),
                postcode=store.get('zipcode'),
                website=store.get('url'),
            )
