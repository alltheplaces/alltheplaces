import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class OrangeESSpider(scrapy.Spider):
    name = "orange_es"
    item_attributes = {"brand": "Orange", "brand_wikidata": "Q1431486"}
    start_urls = ["https://www.orange.es/tiendas"]

    def parse(self, response, **kwargs):
        for store in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var stores =")]/text()').get().split("var stores =")[1],
            json_params={"strict": False},
        ):
            item = Feature()
            item["name"] = store["TradeName"]
            item["street_address"] = " ".join(
                filter(
                    None,
                    [
                        store.get("AddressStreetType_KV"),
                        store.get("AddressStreetName"),
                        store.get("AddressStreetNumber"),
                    ],
                )
            )
            item["postcode"] = store["AddressCP"]
            item["phone"] = store.get("Telephone")
            item["lat"] = store["AddressLat"]
            item["lon"] = store["AddressLong"]
            item["city"] = store["AddressLocationTown"]
            item["state"] = store["AddressLocationProvince"]
            item["website"] = item["ref"] = response.urljoin(store["FriendlyURL"])
            item["opening_hours"] = self.parse_hours(store)
            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            yield item

    def parse_hours(self, store):
        def update_hours(day, hours, oh):
            for hour in hours.split(";"):
                if "-" in hour:
                    oh.add_range(
                        day,
                        hour.split("-")[0].strip(),
                        hour.split("-")[1].strip(),
                    )

        try:
            oh = OpeningHours()
            if hours := store.get("ScheduleMonFri"):
                for day in DAYS[:5]:
                    update_hours(day, hours, oh)
            if hours := store.get("ScheduleSat"):
                update_hours(DAYS[5], hours, oh)
            if hours := store.get("ScheduleSun"):
                update_hours(DAYS[6], hours, oh)

            return oh
        except:
            return None
