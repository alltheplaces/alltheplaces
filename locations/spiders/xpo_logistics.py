# -*- coding: utf-8 -*-
import scrapy
import re
import ast
from locations.items import GeojsonPointItem

class XPOLogisticsSpider(scrapy.Spider):
    name = "xpo_logistics"
    brand = "XPO Logistics"
    allowed_domains = ["www.xpo.com"]
    start_urls = (
        'https://www.xpo.com/global-locations/',
    )

    def parse(self, response):
        script = response.xpath('//script[contains(.,"globalLocationsArray")]').extract_first()
        data = re.search(r'globalLocationsArray = (.*);', script).groups()[0]
        data = ast.literal_eval(data)

        for store in data:
            yield GeojsonPointItem(
                lat=float(store['latitude']),
                lon=float(store['longitude'].replace(',','')),
                phone=store['telephone'],
                ref=store['office_name'],
                addr_full=store['street'],
                city=store['city'],
                state=store['state'],
                postcode=store['postal_code'],
                country=store['country'],
                name=store['office_name']
            )


