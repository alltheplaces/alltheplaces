import html
import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CarlsJrUSSpider(SitemapSpider, StructuredDataSpider):
    name = "carls_jr_us"
    item_attributes = {"brand": "Carl's Jr.", "brand_wikidata": "Q1043486"}
    sitemap_urls = ["https://locations.carlsjr.com/robots.txt"]
    sitemap_rules = [(r"^https://locations\.carlsjr\.com/[a-z]{2}/[^/]+/[^/]+/?$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["street_address"] = html.unescape(item["street_address"])
        item["city"] = html.unescape(item["city"])
        if ref := re.match(r".+ (\d+)$", item.pop("name")):
            item["ref"] = ref.group(1)

        features = response.xpath(
            '//*[@itemprop="makesOffer"][not(@style="display: none;")]//*[@itemprop="name"]/text()'
        ).getall()
        apply_yes_no(Extras.WIFI, item, "Wifi" in features)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Wifi" in features)
        apply_category(Categories.FAST_FOOD, item)
        yield item
