import scrapy

from locations.hours import DAYS_BG, OpeningHours, sanitise_day
from locations.items import Feature


class A1BGSpider(scrapy.Spider):
    name = "a1_bg"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q1941592", "country": "BG"}
    allowed_domains = ["www.a1.bg"]
    start_urls = ["https://www.a1.bg/1/mm/shops/mc/index/ma/index/mo/1?ajaxaction=getShopsWithWorkTime"]

    def parse(self, response):
        for store in response.json()["response"]:
            item = Feature()
            item["ref"] = store["id"]
            item["name"] = store["name"]
            item["addr_full"] = store["address"].strip()
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["phone"] = store["phone"]
            item["opening_hours"] = self.get_opening_hours(store, item["ref"])
            yield item

    def get_opening_hours(self, store, ref):
        try:
            o = OpeningHours()
            for day in store["worktime"]:
                if (
                    (workdays := day.get("workday").split("-"))
                    and (hour_from := day.get("hour_from"))
                    and (hour_to := day.get("hour_to"))
                ):
                    for workday in workdays:
                        o.add_range(sanitise_day(workday, DAYS_BG), hour_from, hour_to, "%H:%M")

            return o.as_opening_hours()
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours for {ref}, {e}")
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
