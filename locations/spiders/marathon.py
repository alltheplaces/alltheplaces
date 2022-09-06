# -*- coding: utf-8 -*-
import scrapy
from locations.dict_parser import DictParser


class MarathonSpider(scrapy.spiders.CSVFeedSpider):
    name = "marathon"
    item_attributes = {
        "brand": "Marathon Petroleum",
        "brand_wikidata": "Q458363",
        "country": "US",
    }
    start_urls = [
        "https://www.marathonbrand.com/content/includes/mpc-brand-stations/SiteList.csv"
    ]
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"

    def parse_row(self, response, row):
        if row["Status"] == "Open":
            row["street_address"] = row.pop("Address")
            row["id"] = row.pop("StoreNumber")
            yield DictParser.parse(row)
