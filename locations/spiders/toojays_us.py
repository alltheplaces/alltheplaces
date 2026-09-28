from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class ToojaysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "toojays_us"
    item_attributes = {"brand": "TooJay's"}
    sitemap_urls = ["https://www.toojays.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item.pop("name", None)
        item.pop("image", None)
        item["branch"] = response.xpath("normalize-space(//h1)").get()

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "sandwich"
        item["extras"]["website:menu"] = response.urljoin("/menus/toojays-menu/")
        item["extras"]["website:orders"] = response.xpath('//a[.//span[normalize-space()="Order Online"]]/@href').get()

        yield item
