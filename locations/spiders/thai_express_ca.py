import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class ThaiExpressCASpider(SitemapSpider, StructuredDataSpider):
    name = "thai_express_ca"
    item_attributes = {"brand": "Thaï Express", "brand_wikidata": "Q7711610"}
    sitemap_urls = ["https://locations.thaiexpress.ca/sitemap.xml"]
    sitemap_rules = [(r"https://locations\.thaiexpress\.ca/(?:qc|on|ab|bc|ns|mb|sk|nb|nl|pe)/[^/]+/[^/]+$", "parse_sd")]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response):
            if ld_obj.get("credentialSubject"):
                yield ld_obj["credentialSubject"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        branch = re.sub(r"^Tha[iï] Express( Restaurant)?\s*", "", item.pop("name", "") or "").strip()
        item["branch"] = branch or None
        item["image"] = None

        apply_category(Categories.FAST_FOOD, item)

        yield item
