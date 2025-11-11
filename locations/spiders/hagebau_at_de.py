import re

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class HagebauATDESpider(StructuredDataSpider):
    name = "hagebau_at_de"
    item_attributes = {"brand": "Hagebaumarkt", "brand_wikidata": "Q1568279"}
    start_urls = ["https://www.hagebau.de/marktfinder/", "https://www.hagebau.at/marktfinder/"]

    def parse(self, response: Response, **kwargs):
        for url, lat, lon in re.findall(
            r"url:\s*\'([0-9a-z-/]+)\',\s*.+lat\":(\d+\.\d+),\s*\"lon\":(\d+\.\d+)",
            response.xpath('//@*[name()=":initial-stores"]').get().replace("...", ""),
        ):
            yield scrapy.Request(
                url=response.url.replace("/marktfinder/", "") + url,
                callback=self.parse_sd,
                meta=dict(store_info={"lat": lat, "lon": lon}),
            )

    def post_process_item(self, item, response, ld_data, **kwargs):
        store = response.meta["store_info"]
        item["lat"] = store["lat"]
        item["lon"] = store["lon"]
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        oh = OpeningHours()
        for day_time in ld_data["openingHoursSpecification"]:
            open_time = day_time["opens"]
            close_time = day_time["closes"]
            for day in day_time["dayOfWeek"]:
                day = sanitise_day(day, DAYS_DE)
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh

        yield item
