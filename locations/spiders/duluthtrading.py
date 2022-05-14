# -*- coding: utf-8 -*-
import json

import scrapy
from locations.items import GeojsonPointItem


class DuluthTradingSpider(scrapy.Spider):
    name = "duluthtrading"
    item_attributes = {"brand": "Duluth Trading", "brand_wikidata": "Q48977107"}
    allowed_domains = ["duluthtrading.com"]
    start_urls = ["https://www.duluthtrading.com/find-stores/?brand=duluth"]

    def parse(self, response):
        locations = json.loads(response.xpath("//div/@data-storejson").extract_first())
        for data in locations:
            street = data.get("address1")
            city = data.get("city")
            ref = data.get("id")
            properties = {
                "name": data.get("name"),
                "ref": ref,
                "street": street,
                "city": city,
                "postcode": data.get("postalCode"),
                "state": data.get("stateCode"),
                "country": data.get("countryCode"),
                "phone": data.get("phone"),
                "website": f"https://www.duluthtrading.com/locations/?StoreID={ref}&street-address={street}&city={city}",
                "lat": float(data.get("latitude", 0)),
                "lon": float(data.get("longitude", 0)),
            }
            yield GeojsonPointItem(**properties)
