from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaMXXSpider(JSONBlobSpider):
    name = "toyota_mx"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = ["https://www.toyota.mx/distribuidores"]
    locations_key = "response"

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_state)

    def fetch_state(self, response):
        states = response.xpath(
            './/form[@data-distribuidores="https://www.toyota.mx/api/distribuidores"]/.//option/@value'
        ).getall()
        states = [s for s in states if s.strip() != ""]
        for state in states:
            yield JsonRequest(
                f"https://www.toyota.mx/api/distribuidores?estado={state}&tipo=mapa",
                callback=self.parse,
                meta={"state": state},
            )

    def pre_process_data(self, location):
        location["ref"] = location.pop("tid")

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_CAR, item)  # No data available on different category/extra features
        item["state"] = response.meta["state"]
        item["image"] = location["uri"]
        item["addr_full"] = clean_address(location["description"]).replace("<p>", "").replace("</p>", "")
        yield JsonRequest(
            url=f"https://www.toyota.mx/api/geo?distribuidor={item['ref']}&tipo=distribuidor",
            meta={"item": item},
            callback=self.parse_dealer,
        )

    def parse_dealer(self, response):
        item = response.meta["item"]
        location = response.json()
        item["email"] = location["email"].replace(",", ";")
        item["website"] = location.get("sitio")

        item["opening_hours"] = OpeningHours()
        for key, days in {
            "lunesviernes": "Mo-Fr",
            "sabado": "Sa",
            "domingo": "Su",
        }.items():
            if times := location.get(key):
                item["opening_hours"].add_ranges_from_string(f"{days} {times.replace("a.m.", "").replace("p.m.", "")}")
            else:
                try:
                    item["opening_hours"].set_closed(days)
                except ValueError:
                    item["opening_hours"].set_closed(DAYS_WEEKDAY)

        yield item
