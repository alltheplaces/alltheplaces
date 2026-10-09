from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BigBoyUSSpider(SitemapSpider, StructuredDataSpider):
    name = "big_boy_us"
    item_attributes = {"brand": "Big Boy", "brand_wikidata": "Q4386779"}
    allowed_domains = ["www.bigboy.com"]
    sitemap_urls = ["https://www.bigboy.com/robots.txt"]
    sitemap_rules = [(r"/locations/[-\w]+", "parse_sd")]
    drop_attributes = {"facebook", "image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Big Boy ")
        item["opening_hours"] = OpeningHours()
        hours = response.xpath('normalize-space(//span[contains(., "Hours:")])').get("").replace("Hours:", "")
        item["opening_hours"].add_ranges_from_string("Mo-Su: {}".format(hours))
        apply_category(Categories.RESTAURANT, item)
        yield item
