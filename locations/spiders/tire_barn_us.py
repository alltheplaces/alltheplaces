from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TireBarnUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tire_barn_us"
    item_attributes = {"brand": "Tire Barn Warehouse"}
    allowed_domains = ["locations.tirebarn.com"]
    sitemap_urls = ["https://locations.tirebarn.com/sitemap_index.xml"]
    sitemap_rules = [(r"^https://locations\.tirebarn\.com/[a-z]{2}/[^/]+/([^/]+)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    time_format = "%H:%M:%S"
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        item["ref"] = response.url.replace("https://locations.tirebarn.com/", "")
        item["name"] = None
        item["branch"] = item.get("city")
        item["website"] = response.url

        apply_category(Categories.SHOP_TYRES, item)

        yield item
