import chompjs
import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SignatureCosmeticsZASpider(scrapy.Spider):
    name = "signature_cosmetics_za"
    item_attributes = {
        "brand": "Signature Cosmetics & Fragrances",
        "brand_wikidata": "Q116894514",
    }
    start_urls = ["https://signaturecosmetics.co.za/pages/store-locator"]
    no_refs = True

    def parse(self, response):
        raw_data = chompjs.parse_js_object(
            response.xpath("//script[contains(text(), 'storeLocatorData')]/text()").get()
        )
        for store in raw_data[0]["locations"]:
            item = DictParser.parse(store)
            item["branch"] = store["OrgUnitName"]
            item["postcode"] = str(item["postcode"])
            item["opening_hours"] = OpeningHours()
            for day_time in store["Schedule"]:
                day = day_time["Day"]
                open_time = day_time["StartTime"]
                close_time = day_time["EndTime"]
                item["opening_hours"].add_range(
                    day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S"
                )
            yield item
