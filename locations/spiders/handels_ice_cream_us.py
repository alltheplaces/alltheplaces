import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider, extract_facebook, extract_instagram


class HandelsIceCreamUSSpider(SitemapSpider, StructuredDataSpider):
    name = "handels_ice_cream_us"
    item_attributes = {"brand": "Handel's Homemade Ice Cream", "brand_wikidata": "Q16983222"}
    sitemap_urls = ["https://handelsicecream.com/sitemap.xml"]
    sitemap_rules = [(r"/store/([^/]+)/$", "parse_sd")]
    wanted_types = ["FoodEstablishment"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if "coming soon" in response.xpath('//h6[@class="store-open"]/text()').get("").lower():
            return

        item["lat"] = ld_data.get("latitude")
        item["lon"] = ld_data.get("longitude")
        item["branch"] = re.sub(r"^Handel[’']?s\s+Homemade\s+Ice\s+Cream\s+", "", item.pop("name"))

        # Brand-wide social accounts also appear in the page footer
        if address_block := response.xpath('//div[contains(@class, "address")]'):
            extract_facebook(item, address_block)
            extract_instagram(item, address_block)

        apply_category(Categories.ICE_CREAM, item)

        yield item
