from collections.abc import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CinnaholicUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cinnaholic_us"
    item_attributes = {"brand": "Cinnaholic", "brand_wikidata": "Q48965480"}
    sitemap_urls = ["https://locations.cinnaholic.com/sitemap_index.xml"]
    sitemap_rules = [(r"/ll/us/[a-z]{2}/[^/]+/\d+/$", "parse_sd")]
    wanted_types = ["Bakery"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["email"] = (
            response.xpath('//div[contains(@class, "email contact-item hide")]/@class')
            .get()
            .removeprefix("email contact-item hide")
        )

        apply_category(Categories.SHOP_BAKERY, item)

        yield item
