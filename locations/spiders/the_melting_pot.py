import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TheMeltingPotSpider(CrawlSpider, StructuredDataSpider):
    name = "the_melting_pot"
    item_attributes = {"brand": "The Melting Pot", "brand_wikidata": "Q7750948"}
    start_urls = ["https://www.meltingpot.com/restaurant-locations.aspx"]
    rules = [
        Rule(LinkExtractor(allow=r"meltingpot\.com/[a-z0-9-]+-[a-z]{2}/?$", deny=r"about-us"), callback="parse_sd")
    ]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item.pop("name", None).removeprefix("Melting Pot ").removeprefix("The Melting Pot ")
        item.pop("image", None)
        # The page's map script carries the coordinates; the structured data does not.
        if match := re.search(r"'lat':\s*(-?\d+\.\d+),\s*'lng':\s*(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = match.groups()
        apply_category(Categories.RESTAURANT, item)
        yield item
