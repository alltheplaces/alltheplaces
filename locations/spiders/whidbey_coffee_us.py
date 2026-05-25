import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class WhidbeyCoffeeUSSpider(SitemapSpider):
    name = "whidbey_coffee_us"
    item_attributes = {"brand": "Whidbey Coffee"}
    allowed_domains = ["www.whidbeycoffee.com"]
    sitemap_urls = ("https://www.whidbeycoffee.com/sitemap.xml",)
    sitemap_rules = [(r"/pages/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_block = response.xpath('//p[strong[contains(text(), "Location") or contains(text(), "Address")]]')
        if not location_block:
            return

        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//h1/text()").get("").strip()

        iframe_src = response.xpath('//iframe[contains(@src, "maps")]/@src').get("")
        if m := re.search(r"!3d(-?[\d.]+).*!2d(-?[\d.]+)|!2d(-?[\d.]+).*!3d(-?[\d.]+)", iframe_src):
            lat3, lon2, lon2b, lat3b = m.groups()
            item["lat"] = lat3 or lat3b
            item["lon"] = lon2 or lon2b
        elif m := re.search(r"/@(-?[\d.]+),(-?[\d.]+)", response.text):
            item["lat"], item["lon"] = m.groups()

        address_lines = [t.strip() for t in location_block.xpath(".//a//text()").getall() if t.strip()]
        if address_lines:
            item["addr_full"] = ", ".join(address_lines)

        phone_block = response.xpath('//p[strong[contains(text(), "Phone")]]')
        if phone_block:
            phone_text = " ".join(t.strip() for t in phone_block.xpath(".//text()").getall() if t.strip())
            item["phone"] = re.sub(r"(?i)^phone:?\s*", "", phone_text).strip()

        apply_category(Categories.COFFEE_SHOP, item)
        yield item
