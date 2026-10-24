from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AudilabFRSpider(SitemapSpider, StructuredDataSpider):
    name = "audilab_fr"
    item_attributes = {"brand": "Audilab", "brand_wikidata": "Q117352010"}
    sitemap_urls = ["https://www.audilab.fr/center-sitemap.xml"]
    sitemap_rules = [(r"^https://www\.audilab\.fr/centre/[^/]+/$", "parse_sd")]
    search_for_facebook = False
    search_for_email = False

    def post_process_item(self, item: Feature, response: TextResponse, raw_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Audilab / Audioprothésiste ")

        if item.get("phone") == "+33":
            item["phone"] = None
        elif (item.get("phone") or "").startswith("+33+33"):
            item["phone"] = item["phone"].removeprefix("+33")

        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
