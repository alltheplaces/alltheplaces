import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class AutoNationUSSpider(SitemapSpider, StructuredDataSpider):
    name = "auto_nation_us"
    allowed_domains = ["autonation.com"]
    item_attributes = {"brand": "AutoNation", "brand_wikidata": "Q784804"}
    sitemap_urls = ["https://www.autonation.com/robots.txt"]
    sitemap_rules = [(r"https://www.autonation.com/dealers/[^/]+$", "parse")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        store_data = json.loads(response.xpath('//script[@id="store-detail-state"]/text()').get())
        store_info = DictParser.get_nested_key(store_data, "storeInfo")
        item["lat"] = store_info.get("latitude")
        item["lon"] = store_info.get("longitude")
        item["ref"] = store_info.get("hyperionId")
        # ld_data has opening hours of sales and services all merged, difficult to differentiate.
        item["opening_hours"] = self.parse_opening_hours(store_info.get("detailedHours") or [])
        departments = [department.get("name") for department in store_info.get("departments", [])]
        if "Sales" in departments:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, "Service" in departments or "Collision" in departments)
        else:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = DAYS[rule["day"]]
            if rule.get("startTime") and rule.get("endTime"):
                oh.add_range(day, rule["startTime"], rule["endTime"], "%I:%M %p")
            else:
                oh.set_closed(day)
        return oh
