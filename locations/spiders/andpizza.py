# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class TacocabanaSpider(scrapy.Spider):
    name="andpizza"
    allowed_domains = ["andpizza.com"]
    start_urls = (
        "https://andpizza.com",
    )

    def store_hours(self, store_hours):
        ret = ""
        for i in range(len(store_hours)):
            if store_hours[i] == "&bar":
                break

            ret += store_hours[i]
            if i % 2 == 1 and i != len(store_hours) - 1:
                ret += ", "
            elif i % 2 == 0:
                ret += ":"

        return ret

    def parse(self, response):
        selector = scrapy.Selector(response)
        stores = selector.css("div.location")

        for store in stores:
            ref = store.css("div.location::attr(class)").extract()[0].split(" ")[1]
            name = store.css("a.knockout *::text").extract()[0]
            address = store.css("address>a *::text").extract()
            address1 = address[0]
            address2 = address[len(address)-1].split(",")
            hours = store.css("div.hours")

            store_hours = ""
            if not hours.css("span>a"):
                store_hours = self.store_hours(store.css("div.hours *::text").extract())

            properties = {
                "ref": ref,
                "name": name,
                "street": address1,
                "city": address2[0],
                "state": address2[1].split(" ")[1],
                "postcode": address2[1].split(" ")[2],
                "opening_hours": store_hours
            }

            yield GeojsonPointItem(**properties)

