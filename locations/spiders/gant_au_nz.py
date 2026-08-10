import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class GantAUNZSpider(Spider):
    name = "gant_au_nz"
    item_attributes = {"brand": "GANT", "brand_wikidata": "Q1493667"}
    allowed_domains = ["gant.com.au"]
    start_urls = ["https://gant.com.au/pages/stores"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.xpath("//store-locator-marker"):
            raw_name = location.xpath("@data-name").get()
            item = Feature()
            item["ref"] = raw_name.replace('"', "").replace(" ", "_").lower().strip()
            item["branch"] = raw_name
            item["addr_full"] = location.xpath("@data-address").get()
            item["phone"] = location.xpath("@data-phone").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()

            state_raw = location.xpath("@data-state").get()
            if state_raw == "New Zealand":
                item["country"] = "NZ"
            else:
                item["country"] = "AU"
                item["state"] = state_raw

            if hours_raw := location.xpath("@data-hours").get():
                item["opening_hours"] = OpeningHours()
                hours_spaced = re.sub(r"(?<!^)(Mon|Tue|Wed|Thu|Fri|Sat|Sun)", r" \1", hours_raw)
                item["opening_hours"].add_ranges_from_string(hours_spaced)

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
