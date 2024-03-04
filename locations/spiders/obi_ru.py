import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours
from locations.spiders.obi_eu import OBI_SHARED_ATTRIBUTES


class ObiRUSpider(scrapy.Spider):
    name = "obi_ru"
    allowed_domains = ["obi.ru"]
    item_attributes = OBI_SHARED_ATTRIBUTES
    start_urls = ["https://obi.ru/graphql?hash=2872797852"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "RU"

    def parse(self, response):
        for poi in response.json()["data"]["offlineStores"]:
            if poi["source_code"] in ["668", "default"]:
                # Exclude test pois
                continue
            item = DictParser.parse(poi)
            item["ref"] = poi["source_code"]
            if not poi["enabled"]:
                item["extras"]["end_date"] = "yes"
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string(poi.get("schedule"), DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f'Fail to parse hours: {poi.get("schedule")}, {e}')
            yield item
