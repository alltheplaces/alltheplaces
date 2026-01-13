import json

from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.jysk import urljoin


class DominosPizzaNOSpider(Spider):
    name = "dominos_pizza_no"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["www.dominos.no"]
    start_urls = ["https://www.dominos.no/butikker"]

    def parse(self, response):
        location_data = json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get())
        for store in location_data["props"]["pageProps"]["stores"]:
            yield self.parse_store(store)

    def parse_store(self, store):
        item = DictParser.parse(store)

        item["ref"] = store.get("externalId")
        item["name"] = "Domino's " + store["name"]
        item["branch"] = store.get("name")
        item["phone"] = store.get("localPhoneNumber")
        item["website"] = urljoin("https://www.dominos.no/no/butikker/", store.get("slug"))

        item["street_address"] = item.pop("street", "")
        item.pop("state")  # Remove invalid state field

        if address := store.get("address"):
            if location := address.get("location"):
                item["lat"] = location.get("latitude")
                item["lon"] = location.get("longitude")

        delivery_options = store.get("deliveryOptions", {})
        apply_yes_no(Extras.DELIVERY, item, delivery_options.get("delivery", {}).get("active"))
        apply_yes_no(Extras.TAKEAWAY, item, delivery_options.get("carryout", {}).get("active"))

        if carryout_hours := delivery_options.get("carryout", {}).get("hoursOfOperation"):
            item["opening_hours"] = self.parse_hours(carryout_hours)

        if delivery_hours := delivery_options.get("delivery", {}).get("hoursOfOperation"):
            if oh := self.parse_hours(delivery_hours):
                item["extras"]["opening_hours:delivery"] = oh.as_opening_hours()

        return item

    @staticmethod
    def parse_hours(hours):
        oh = OpeningHours()
        for entry in hours:
            oh.add_range(entry.get("weekDay"), entry.get("openingHours"), entry.get("closingHours"))
        return oh
