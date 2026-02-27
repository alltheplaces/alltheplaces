import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EuroCarPartsIESpider(CrawlSpider, StructuredDataSpider):
    name = "euro_car_parts_ie"
    allowed_domains = ["www.eurocarparts.com"]
    start_urls = ["https://www.eurocarparts.com/en_ie/store-locator"]
    item_attributes = {"brand": "Euro Car Parts", "brand_wikidata": "Q23782692"}
    search_for_facebook = False
    search_for_twitter = False
    rules = [Rule(LinkExtractor(allow=r"/en_ie/[\w-]+\.html$", deny="sitemap"), callback="parse_sd")]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.split("/")[-1].removesuffix(".html")
        item["branch"] = item.pop("name").removeprefix("Euro Car Parts  -")
        item["postcode"] = None  # Microdata has "EIRE" which isn't a valid postcode
        item["lat"], item["lon"] = re.search(r"LatLng\(([-\d.]+), ([-\d.]+)\)", response.text).groups()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(" ".join(response.css(".timing-table .data ::text").getall()))
        apply_category(Categories.SHOP_CAR_PARTS, item)
        yield item
