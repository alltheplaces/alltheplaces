import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BvlgariSpider(SitemapSpider, StructuredDataSpider):
    name = "bvlgari"
    allowed_domains = ["www.bulgari.com"]
    item_attributes = {"brand": "Bulgari", "brand_wikidata": "Q752515"}
    sitemap_urls = ["https://www.bulgari.com/robots.txt"]
    sitemap_follow = ["/sitemap-pages-en-gb"]
    sitemap_rules = [(r"/en-gb/storelocator/country-region/[^/]+/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["JewelryStore"]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Pages carry both ld+json and Microdata; the ld+json has duplicate refs and no
        # coordinates, so disable it and parse the Microdata.
        for ld in response.xpath('//script[@type="application/ld+json"]'):
            ld.root.set("type", "nop")
        yield from self.parse_sd(response)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        # Only Bvlgari boutiques; the rest are authorised resellers.
        if response.xpath('normalize-space(//div[@class="Hero-storeType"]/text())').get() != "Bvlgari Boutique":
            return
        item.pop("image", None)  # brand-wide stock image, not per-store
        item["city"] = response.xpath('//span[@class="Address-field Address-city"]/text()').get()
        if name := item.pop("name", None):
            item["branch"] = re.sub(r"^bvlgari\s+", "", name, flags=re.I)
        apply_category(Categories.SHOP_FASHION_ACCESSORIES, item)
        yield item
