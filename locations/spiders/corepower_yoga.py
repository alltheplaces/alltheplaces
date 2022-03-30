# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class CorePowerYogaSpider(scrapy.Spider):
    name = "corepower_yoga"
    item_attributes = {"brand": "Corepower Yoga"}
    allowed_domains = ["www.corepoweryoga.com"]
    start_urls = ("https://www.corepoweryoga.com/data/all-locations",)

    def parse(self, response):
        results = response.json()
        for index, data in results.items():
            if index != "pager" and data["field_comp_studio"] != "Not Yet Open":
                properties = {
                    "ref": data["drishti_id"],
                    "name": data["title"],
                    "lat": data["latitude"],
                    "lon": data["longitude"],
                    "addr_full": data["Address 1"],
                    "city": data["City"],
                    "state": data["Studio State"],
                    "phone": data["Phone"],
                    "website": "https://www.corepoweryoga.com%s" % (data["path"]),
                }
                yield GeojsonPointItem(**properties)
