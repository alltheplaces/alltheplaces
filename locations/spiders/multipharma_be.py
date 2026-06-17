import json
from typing import Iterable

import scrapy
from scrapy.http import Response
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MultipharmaBESpider(scrapy.Spider):
    name = "multipharma_be"
    item_attributes = {"brand": "Multipharma", "brand_wikidata": "Q62565018"}
    start_urls = [
        "https://www.multipharma.be/on/demandware.store/Sites-Multipharma-Webshop-BE-Site/nl_BE/Stores-FindStores?format=ajax"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response) -> Iterable[scrapy.Request]:
        data = response.json()
        locations = json.loads(data.get("locations", "[]"))
        for location in locations:
            sel = Selector(text=location.get("infoWindowHtml", ""))
            detail_url = sel.xpath('//a[contains(@href, "/onze-apotheken/detail/")]/@href').get()
            yield scrapy.Request(url=response.urljoin(detail_url), callback=self.parse_detail)

    def parse_detail(self, response: Response) -> Iterable[Feature]:
        store_data = response.xpath("//*[@data-store]/@data-store").get()
        if not store_data:
            return
        data = json.loads(store_data)
        data["street"] = data.pop("address1")
        data["housenumber"] = data.pop("address2")

        item = DictParser.parse(data)
        item["ref"] = data.get("ID")
        item["branch"] = data.get("name", "").title()
        item["website"] = response.url
        item["opening_hours"] = self.parse_opening_hours(data)

        apply_category(Categories.PHARMACY, item)
        yield item

    def parse_opening_hours(self, data: dict) -> OpeningHours:
        oh = OpeningHours()
        for day_index, day in enumerate(DAYS):
            am_from = data.get(f"storeHoursAMFrom_{day_index}")
            am_to = data.get(f"storeHoursAMTo_{day_index}")
            pm_from = data.get(f"storeHoursPMFrom_{day_index}")
            pm_to = data.get(f"storeHoursPMTo_{day_index}")
            if am_from and am_to:
                oh.add_range(day, am_from, am_to)
            if pm_from and pm_to:
                oh.add_range(day, pm_from, pm_to)
        return oh
