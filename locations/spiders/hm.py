import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class HMSpider(scrapy.Spider):
    name = "hm"
    item_attributes = {"brand": "H&M", "brand_wikidata": "Q188326"}
    start_urls = ["http://www.hm.com/entrance.ahtml"]
    requires_proxy = True

    def parse(self, response):
        for country_code in response.xpath("//@data-location").getall():
            yield scrapy.Request(
                url=f"https://api.storelocator.hmgroup.tech/v2/brand/hm/stores/locale/en_us/country/{country_code}?_type=json&campaigns=true&departments=true&openinghours=true",
                callback=self.parse_country,
            )

    def parse_country(self, response):
        for store in response.json()["stores"]:
            store.update(store.pop("address"))
            store["street_address"] = ", ".join(filter(None, [store.get("streetName1"), store.get("streetName2")]))

            item = DictParser.parse(store)

            item["ref"] = store["storeCode"]
            item["extras"] = {"storeClass": store.get("storeClass")}

            oh = OpeningHours()
            for rule in store["openingHours"]:
                oh.add_range(rule["name"], rule["opens"], rule["closes"])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
