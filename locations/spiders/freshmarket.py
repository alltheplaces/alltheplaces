# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class FreshMarketSpider(scrapy.Spider):
    name = "freshmarket"
    item_attributes = {"brand": "Fresh Market", "brand_wikidata": "Q7735265"}
    allowed_domains = ["thefreshmarket.com"]
    start_urls = ("https://www.thefreshmarket.com/your-market/store-locator/",)

    def parse(self, response):
        json_data = response.xpath(
            '//script[@data-reactid="41"]/text()'
        ).extract_first()
        start = json_data.index('"stores":') + 9
        data = json.decoder.JSONDecoder().raw_decode(json_data, start)[0]
        allStores = data["allStores"]
        for store in allStores:

            properties = {
                "name": store["storeName"],
                "ref": store["storeNumber"],
                "addr_full": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["postalCode"],
                "phone": store["phoneNumber"],
                "website": "https://www.thefreshmarket.com/my-market/store/"
                + store["slug"],
                "opening_hours": store["moreStoreHours"],
                "lat": float(store["storeLocation"]["lat"]),
                "lon": float(store["storeLocation"]["lon"]),
            }

            yield GeojsonPointItem(**properties)
