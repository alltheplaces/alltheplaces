# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json

class WholeFoodsSpider(scrapy.Spider):
    name = "whole_foods"
    brand = "Whole Foods"
    allowed_domains = ["www.wholefoodsmarket.com"]
    start_urls = (
        'https://www.wholefoodsmarket.com/ajax/stores',
    )

    def parse_phone(self, phone):
        phone = phone.replace('.','')
        phone = phone.replace(')','')
        phone = phone.replace('(','')
        phone = phone.replace('_','')
        phone = phone.replace('-','')
        phone = phone.replace('+','')
        phone = phone.replace(' ','')
        return phone

    def parse(self, response):
        json_string = json.loads(response.xpath("./body/p/text()").extract_first())
        for item in json_string:
            thisItem = json_string[item]
            if thisItem["phone"] is None:
                phoneString=""
            else:
                phoneString=self.parse_phone(thisItem["phone"])

            yield GeojsonPointItem(
                ref=thisItem["storename"],
                addr_full=thisItem["location"]["street"],
                city=thisItem["location"]["city"],
                state=thisItem["location"]["stateabbr"],
                postcode=thisItem["location"]["zip"],
                phone=phoneString,
                country=thisItem["location"]["country"],
                lat=float(thisItem["location"]["lat"]),
                lon=float(thisItem["location"]["lon"]),
            )

