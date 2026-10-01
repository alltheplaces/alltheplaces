from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.open_graph_spider import OpenGraphSpider


class BudgensGBSpider(SitemapSpider, OpenGraphSpider):
    name = "budgens_gb"
    item_attributes = {"brand": "Budgens", "brand_wikidata": "Q4985016"}
    sitemap_urls = ["https://www.budgens.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse")]

    def post_process_item(self, item: Feature, response: Response, **kwargs: Any) -> Any:
        item["street_address"] = item["street_address"].strip(",")

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//tr[contains(@class, "office-hours__item")]'):
            day = rule.xpath('./td[contains(@class, "office-hours__item-label")]/text()').get("").strip(" :")
            slots = rule.xpath('./td[contains(@class, "office-hours__item-slots")]/text()').get("").strip()
            if not day or not slots:
                continue
            if slots.lower() == "all day open":
                item["opening_hours"].add_range(day, "00:00", "24:00")
            else:
                item["opening_hours"].add_ranges_from_string(f"{day} {slots}")

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
