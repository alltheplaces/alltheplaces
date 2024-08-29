import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class XlBygNOSpider(scrapy.Spider):
    name = "xl_byg_no"
    item_attributes = {"brand": "XL-BYG", "brand_wikidata": "Q10720798"}
    start_urls = [
        "https://api.xlbygg.getadigital.cloud/store/stores?customProperty.Key=web&customProperty.Value=xlbygg"
    ]

    def parse(self, response, **kwargs):
        for store in response.json():
            item = DictParser.parse(store)
            item["website"] = f'https://www.xl-bygg.no/?store={item["ref"]}'
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                timing = store["openingHours"].get(day.lower(), {})
                if timing.get("isOpen"):
                    item["opening_hours"].add_range(day, timing["openFrom"], timing["openTo"], time_format="%H:%M:%S")
            yield item
