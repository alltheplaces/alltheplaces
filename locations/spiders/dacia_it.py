import re

import scrapy

from locations.dict_parser import DictParser


class DaciaItSpider(scrapy.Spider):
    name = "dacia_it"
    item_attributes = {
        "brand": "Dacia",
        "brand_wikidata": "Q27460",
    }
    allowed_domains = ["dacia.it"]
    start_urls = ["https://www.dacia.it/concessionario/lista-concessionari.data?page=0"]

    def parse(self, response):
        data = (
            response.json()
            .get("content", {})
            .get("editorialZone", {})
            .get("slice54vb", {})
            .get("dealers", {})
            .get("data")
        )
        for row in data:
            item = DictParser.parse(row)
            item["ref"] = row.get("birId")
            item["street_address"] = row.get("address", {}).get("extendedAddress")
            item["lat"] = row.get("geolocalization", {}).get("lat")
            item["lon"] = row.get("geolocalization", {}).get("lon")
            item["phone"] = row.get("telephone")

            yield item

        page = int(re.findall("[0-9]+", response.url)[0]) + 1
        if data:
            url = f"https://www.dacia.it/concessionario/lista-concessionari.data?page={page}"
            yield scrapy.Request(url=url, callback=self.parse)
