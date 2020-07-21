# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    'Mon': 'Mo',
    'Tue': 'Tu',
    'Wed': 'We',
    'Thu': 'Th',
    'Fri': 'Fr',
    'Sat': 'Sa',
    'Sun': 'Su'
}

class ReiSpider(scrapy.Spider):
    name = "rei"
    allowed_domains = ["www.rei.com"]
    start_urls = (
        'https://www.rei.com/map/store',
    )

    # Fix formatting for ["Mon - Fri 10:00-1800","Sat 12:00-18:00"]
    def format_days(self, range):
        pattern = r'^(.{3})( - (.{3}) | )(\d.*)'
        start_day, seperator, end_day, time_range = re.search(pattern, range.strip()).groups()
        result = DAY_MAPPING[start_day]
        if end_day:
            result += "-"+DAY_MAPPING[end_day]
        result += " "+time_range
        print(result)
        return result

    def fix_opening_hours(self, opening_hours):
        return ";".join(map(self.format_days, opening_hours))
        

    def parse_store(self, response):
        json_string = response.xpath('//script[@id="store-schema"]/text()').extract_first()
        store_dict = json.loads(json_string)
        yield GeojsonPointItem(
            lat=store_dict["geo"]["latitude"],
            lon=store_dict["geo"]["longitude"],
            addr_full=store_dict["address"]["streetAddress"],
            city=store_dict["address"]["addressLocality"],
            state=store_dict["address"]["addressRegion"],
            postcode=store_dict["address"]["postalCode"],
            country=store_dict["address"]["addressCountry"],
            opening_hours=self.fix_opening_hours(store_dict["openingHours"]),
            phone=store_dict["telephone"],
            ref=store_dict["hasMap"] 
        )

    def parse(self, response):
        urls = response.xpath('//a[@class="store-name-link"]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

        
