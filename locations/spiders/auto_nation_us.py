import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class AutoNationUSSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "auto_nation_us"
    allowed_domains = ["autonation.com"]
    item_attributes = {"brand": "AutoNation", "brand_wikidata": "Q784804"}
    sitemap_urls = ["https://www.autonation.com/robots.txt"]
    sitemap_rules = [(r"https://www.autonation.com/dealers/[^/]+$", "parse")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        store_data = json.loads(response.xpath('//script[@id="store-detail-state"]/text()').get())
        store_info = DictParser.get_nested_key(store_data, "storeInfo")
        item["lat"] = store_info.get("latitude")
        item["lon"] = store_info.get("longitude")
        item["ref"] = store_info.get("hyperionId")
        item.pop("image", None)  # Same brand logo on every location, not per-location
        # ld_data has opening hours of sales and services all merged, difficult to differentiate.
        item["opening_hours"] = self.parse_opening_hours(store_info.get("detailedHours") or [])

        departments = [department.get("name") for department in store_info.get("departments", [])]

        if "Sales" in departments:
            sales_item = item.deepcopy()
            sales_item["ref"] = "{}-sales".format(sales_item["ref"])
            apply_category(Categories.SHOP_CAR, sales_item)
            yield sales_item

        if "Service" in departments or "Collision" in departments:
            service_item = item.deepcopy()
            service_item["ref"] = "{}-service".format(service_item["ref"])
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

        if "Sales" not in departments and "Service" not in departments and "Collision" not in departments:
            self.logger.warning("Unknown feature type from provided departments: {}".format(departments.join(";")))

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = DAYS[rule["day"]]
            if rule.get("startTime") and rule.get("endTime"):
                oh.add_range(day, rule["startTime"], rule["endTime"], "%I:%M %p")
            else:
                oh.set_closed(day)
        return oh
