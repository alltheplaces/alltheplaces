from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class HairhouseAUSpider(SitemapSpider, StructuredDataSpider):
    name = "hairhouse_au"
    item_attributes = {"brand": "Hairhouse", "brand_wikidata": "Q118383855"}
    allowed_domains = ["www.hairhouse.com.au"]
    sitemap_urls = ["https://www.hairhouse.com.au/store/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.hairhouse\.com\.au\/store\/[^\/]+$", "parse_sd")]
    wanted_types = ["HealthAndBeautyBusiness"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # The ld+json blob is nested under a non-standard "script:ld+json" wrapper key
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if wrapped := ld_obj.get("script:ld+json"):
                yield wrapped

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Hairhouse ")
        item["addr_full"] = item.pop("street_address", None)
        item.pop("image", None)
        apply_category(Categories.SHOP_HAIRDRESSER_SUPPLY, item)
        yield item
