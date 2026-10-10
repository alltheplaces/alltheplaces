from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BingLeeAUSpider(SitemapSpider, StructuredDataSpider):
    name = "bing_lee_au"
    item_attributes = {"brand": "Bing Lee", "brand_wikidata": "Q4914136"}
    sitemap_urls = ["https://www.binglee.com.au/public/sitemap-locations.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]
    wanted_types = ["ElectronicsStore"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    drop_attributes = {"facebook"}
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = (
            item.pop("name")
            .removeprefix("Bing Lee ")
            .replace("Clearance Outlet", "")
            .replace("Online Sales", "")
            .strip()
        )
        if "Distribution Centre" in item["branch"]:
            item["branch"] = item["branch"].replace("Distribution Centre", "").strip()
            item["name"] = "Bing Lee Distribution Centre"
            item["street_address"] = clean_address(
                item["street_address"].split("not a storefront")[-1].replace(".,", "")
            )
            apply_category(Categories.SHOP_OUTPOST, item)  # Click & Collect Hub Only
        else:
            apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
