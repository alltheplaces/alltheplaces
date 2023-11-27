import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class GoogleOfficesSpider(scrapy.Spider):
    name = "google_offices"
    allowed_domains = ["about.google"]
    item_attributes = {
        "brand": "Google",
        "brand_wikidata": "Q95",
    }
    start_urls = ["https://about.google/locations/data/locations.json"]

    def parse(self, response):
        for poi in response.json().get("offices", []):
            item = DictParser.parse(poi)
            # There are global "regions" in raw data e.g. 'europe', 'asia' etc., not states
            item["state"] = None
            item["image"] = poi.get("image")
            apply_category(Categories.OFFICE_COMPANY, item)
            yield item
