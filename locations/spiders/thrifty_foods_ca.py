from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ThriftyFoodsCASpider(SitemapSpider, StructuredDataSpider):
    name = "thrifty_foods_ca"
    item_attributes = {"brand": "Thrifty Foods", "brand_wikidata": "Q7798140"}
    allowed_domains = ["www.thriftyfoods.com"]
    sitemap_urls = ["https://www.thriftyfoods.com/sitemap/stores/sitemap.xml"]
    sitemap_rules = [(r"/stores/\d+-", "parse_sd")]
    wanted_types = ["GroceryStore"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rsplit("/", 1)[-1].split("-", 1)[0]
        item["branch"] = item.pop("name").removeprefix("Thrifty Foods").strip()

        item["opening_hours"] = OpeningHours()
        for rule in ld_data["openingHoursSpecification"]:
            item["opening_hours"].add_ranges_from_string(rule)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
