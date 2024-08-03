import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RU, DELIMITERS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours
from locations.items import Feature


class MegafonRUSpider(scrapy.Spider):
    name = "megafon_ru"
    allowed_domains = ["www.megafon.ru"]
    item_attributes = {"brand_wikidata": "Q1720713"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.megafon.ru/api/store-locator/map-tile/b2c/"]
    requires_proxy = "RU"

    def parse(self, response):
        offices = response.json()["offices"]
        for id in offices:
            poi = offices[id]
            if poi.get("type") in ["teleport", "green-point", "brand-section"]:
                # Exclude places where only sim cards are sold
                continue
            item = Feature()
            item["ref"] = id
            item["state"] = poi.get("subject")
            item["addr_full"] = poi.get("title")
            item["city"] = poi.get("place")
            item["street"] = poi["street"]
            item["lat"], item["lon"] = poi.get("coords", [None, None])
            self.crawler.stats.inc_value(f"atp/megafon_ru/types/{poi.get('type')}")
            self.parse_hours(item, poi)
            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            if "yota" in poi.get("type", ""):
                # Some Yota stores are present too
                item["brand_wikidata"] = "Q965740"
                item["brand"] = "Yota"
            yield item

    def parse_hours(self, item, poi):
        if worktime := poi.get("worktime", []):
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string(worktime, DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, DELIMITERS_RU)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {worktime}, {item['ref']}, {e}")
