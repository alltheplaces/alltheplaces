from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class KfcATSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_at"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["kfc.co.at"]
    sitemap_urls = ["https://kfc.co.at/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/kfc-[\w-]+$", "parse_sd")]
    wanted_types = ["Restaurant"]
    drop_attributes = {"email", "facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        branch = item.pop("name").removeprefix("KFC ").split(" - Öffnungszeiten")[0]
        if branch.endswith((" mit Drive Through", " mit Drive Thru")):
            branch = branch.rsplit(" mit ", 1)[0]
            apply_yes_no(Extras.DRIVE_THROUGH, item, True)
        item["branch"] = branch
        yield item
