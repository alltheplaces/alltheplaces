# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class CostaCoffeeUSSpider(scrapy.Spider):
    name = "costacoffee_us"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["us.costacoffee.com"]
    start_urls = [
        "https://us.costacoffee.com/locations/",
    ]

    def parse(self, response):
        script = response.xpath(
            '//script[@type="text/x-magento-init"]/text()[contains(.,"js/map")]'
        ).get()
        data = json.loads(script)
        for (ref, store) in data["*"]["js/map"]["locations"].items():
            properties = {
                "ref": ref,
                "name": store["name"],
                "lat": store["lat"],
                "lon": store["long"],
                "street_address": store["address"],
            }
            if m := re.fullmatch("(.*), ?(.*) (.*)", store["address2"]):
                city, state, postcode = m.groups()
                properties.update(
                    {
                        "city": city,
                        "state": state,
                        "postcode": postcode,
                    }
                )
            yield GeojsonPointItem(**properties)
