from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FarmersInsuranceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "farmers_insurance_us"
    item_attributes = {"brand": "Farmers Insurance", "brand_wikidata": "Q1396863"}
    allowed_domains = ["agents.farmers.com"]
    sitemap_urls = ["https://agents.farmers.com/sitemap.xml"]
    sitemap_rules = [(r"https://agents\.farmers\.com/\w{2}/[-\w]+/[-\w]+/?$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").split("/")[-1]
        # Name from JSON-LD is "Agent Name - Street Address" — use agent name as branch
        if " - " in (item.get("name") or ""):
            item["branch"] = item.pop("name").split(" - ")[0].strip()
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
