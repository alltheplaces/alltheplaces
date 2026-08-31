import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SephoraINSpider(SitemapSpider):
    name = "sephora_in"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    sitemap_urls = ["https://sephora.in/sitemap/pages.sitemap.xml"]
    sitemap_rules = [("/page/sephora-", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        name = response.xpath('//div[contains(@class, "store-details-item-bold")]/text()').get()
        if not name or "coming soon" in name.lower():
            return

        item = Feature()
        item["ref"] = response.url.rsplit("/", 1)[-1]
        branch = name.removeprefix("Sephora-").removeprefix("Sephora ").strip().strip("- ")
        item["branch"] = branch
        item["website"] = response.url
        item["country"] = "IN"

        addr_text = response.xpath(
            '//div[contains(@class, "store-details-item")][contains(text(), "Address")]/text()'
        ).get()
        if addr_text:
            item["addr_full"] = re.sub(r"^Address:\s*", "", addr_text).strip()

        phone_text = response.xpath(
            '//div[contains(@class, "store-details-item")][contains(text(), "Phone")]/text()'
        ).get()
        if phone_text:
            item["phone"] = re.sub(r"^Phone:\s*", "", phone_text).strip()

        extract_google_position(item, response)
        self._parse_hours(response, item)

        apply_category(Categories.SHOP_COSMETICS, item)
        yield item

    def _parse_hours(self, response: Response, item: Feature) -> None:
        hours_texts = response.xpath('//div[@class="hours"]/text()').getall()
        if not hours_texts:
            return
        try:
            oh = OpeningHours()
            for hours_text in hours_texts:
                oh.add_ranges_from_string(hours_text)
            item["opening_hours"] = oh
        except Exception:
            pass
