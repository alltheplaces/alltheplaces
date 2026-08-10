import json

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed


class MatalanGBSpider(SitemapSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    allowed_domains = ["www.matalan.co.uk"]
    sitemap_urls = ["https://www.matalan.co.uk/robots.txt"]
    sitemap_rules = [(r"/stores/uk/[^/]+/[^/]+/[^/]+$", "parse")]

    def prep(self, data):
        if isinstance(data, dict):
            return {k: self.prep(data[k]) for k in data.keys()}

        if isinstance(data, list):
            if len(data) == 2 and isinstance(data[0], int):
                return self.prep(data[1])

            return [self.prep(item) for item in data]

        return data

    def parse(self, response: TextResponse, **kwargs):
        for marker in self.prep(
            json.loads(response.xpath("//astro-island[contains(@opts, 'StoreMap')]/@props").get())["markers"]
        ):
            location = marker["store"]
            item = DictParser.parse(location)
            item["phone"] = None
            item["website"] = response.url

            item["opening_hours"] = self.parse_hours(location["openingTimes"])

            if item["name"].startswith("COLLEAGUE ONLY "):
                continue
            if item["name"].startswith("CLOSED "):
                set_closed(item)

            item["branch"] = item.pop("name").split(" - ", 1)[1]
            if item["branch"].endswith(" Clearance"):
                item["branch"] = item["branch"].removesuffix(" Clearance")
                item["name"] = "Matalan Clearance"

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item

    def parse_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            oh.add_range(rule["day"], rule["openingTime"][0:5], rule["closingTime"][0:5])
        return oh
