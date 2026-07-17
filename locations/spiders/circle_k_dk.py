from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CircleKDKSpider(SitemapSpider, StructuredDataSpider):
    name = "circle_k_dk"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    sitemap_urls = ["https://www.circlek.dk/sitemaps/stations/sitemap.xml"]
    sitemap_rules = [(r"/station/(?!ingo-)[-\w]+", "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        rules = ld_data.get("openingHours") or []
        for idx, rule in enumerate(rules):
            if len(rule) == 2:
                rules[idx] = "{} 00:00-24:00".format(rule)
        ld_data["openingHours"] = rules

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        category = Categories.FUEL_STATION
        if item["name"].startswith("CIRCLE K TRUCK ") or item["name"].startswith("TRUCKANLÆG "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K TRUCK ").removeprefix("TRUCKANLÆG ")
            item["name"] = "Circle K Truck"
        elif "TRUCK HOME" in item["name"].replace(",", ""):
            item["name"] = "Circle K Truck"
        elif item["name"].startswith("CIRCLE K MOTORVEJSCENTER "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K MOTORVEJSCENTER ")
            item["name"] = "Circle K Motorvejscenter"
        elif item["name"].startswith("CIRCLE K EV"):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K EV")
            item["name"] = "Circle K"
            category = Categories.CHARGING_STATION
        elif item["name"].startswith("CIRCLE K "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K ")

        extract_google_position(item, response)

        apply_category(category, item)
        yield item
