import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class DaRUSpider(scrapy.Spider):
    name = "da_ru"
    item_attributes = {"brand": "ДА!", "brand_wikidata": "Q127829045"}
    start_urls = ["https://market-da.ru/shops/ajaxmap.html"]

    def parse(self, response):
        for poi in response.json()["markers"]:
            item = Feature()
            item["ref"] = poi["id"]
            item["lon"] = poi["lat"]
            item["lat"] = poi["lon"]
            # City names in nazvadr are inconsistent, sometimes it's a city name, sometimes it's a district name.
            item["addr_full"] = "".join(filter(None, [poi.get("cname"), poi.get("nazvadr")]))
            try:
                oh = OpeningHours()
                hours = poi.get("vrrab")
                if hours := poi.get("vrrab"):
                    hours = hours.replace("с", "").replace(".", ":").strip()
                    open, close = hours.split(" до ")
                    oh.add_days_range(DAYS, open.strip(), close.strip())
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours': {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
