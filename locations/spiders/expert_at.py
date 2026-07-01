import re
from typing import Any

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.structured_data_spider import StructuredDataSpider


class ExpertATSpider(SitemapSpider, StructuredDataSpider):
    name = "expert_at"
    item_attributes = {"brand": "Expert", "brand_wikidata": "Q680990"}
    sitemap_urls = ["https://www.expert.at/sitemap"]
    sitemap_rules = [("/standorte/", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        cleaned = []
        for rule in ld_data.get("openingHours", []):
            rule = re.sub(r"(\d{1,2})\.(\d{2})", r"\1:\2", rule)
            rule = re.sub(r"(?i)geschlossen", "closed", rule)
            if "closed" in rule.lower() or re.search(r"\d{1,2}:\d{2}\s?-\s?\d{1,2}:\d{2}", rule):
                cleaned.append(rule)
        ld_data["openingHours"] = cleaned

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"], item["lon"] = url_to_coords(response.xpath("//a[contains(@href, 'google')]/@href").get())
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
