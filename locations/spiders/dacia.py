import re

import scrapy

from locations.items import GeojsonPointItem


class DaciaSpider(scrapy.Spider):
    name = "dacia"
    item_attributes = {
        "brand": "Dacia",
        "brand_wikidata": "Q27460",
    }
    allowed_domains = ["dacia.fr"]
    start_urls = ["https://www.dacia.fr/wired/commerce/v1/dealers?page=0"]

    def parse(self, response):
        data = response.json().get("data")
        for row in data:
            if not row.get("blacklisted"):
                item = GeojsonPointItem()
                item["ref"] = row.get("dealerId")
                item["name"] = row.get("name")
                item["country"] = row.get("country")
                item["lat"] = row.get("geolocalization", {}).get("lat")
                item["lon"] = row.get("geolocalization", {}).get("lon")
                item["city"] = row.get("regionalDirectorate")
                item["postcode"] = row.get("address", {}).get("postalCode")
                item["street_address"] = row.get("address", {}).get("streetAddress")
                item["phone"] = row.get("telephone", {}).get("value")

                yield item

        if data:
            page = int(re.findall("[0-9]+", response.url)[-1]) + 1
            url = f"https://www.dacia.fr/wired/commerce/v1/dealers?page={page}"
            yield scrapy.Request(url=url, callback=self.parse)
