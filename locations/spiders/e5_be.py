import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class E5BESpider(Spider):
    name = "e5_be"
    item_attributes = {"brand": "e5 Mode", "brand_wikidata": "Q85313633"}
    start_urls = ["https://www.e5.be/nl/kledingwinkels"]

    def parse(self, response, **kwargs):
        data = json.loads(
            response.xpath(
                '//script[@type="text/x-magento-init"][contains(text(), "locator_e5mode_storepickup_locator")]/text()'
            ).get()
        )
        for location in data["[data-role=locator_e5mode_storepickup_locator]"]["e5mode/storeLocator"]["stores"][
            "items"
        ]:
            if location["enabled"] != "1":
                continue

            item = DictParser.parse(location)
            item["lat"], item["lon"] = location["geolocation"].split(",")
            item["ref"] = location["external_id"]
            item["housenumber"] = location["street_nr"]
            item["country"] = location["country_id"]
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                start_time = location.get(f"{day.lower()}_opening")
                end_time = location.get(f"{day.lower()}_close")
                if start_time and end_time:
                    item["opening_hours"].add_range(day, start_time, end_time)
            item["website"] = response.xpath(
                f'//li[@id="store-{location["entity_id"]}"]/div[@class="store-link"]/a/@href'
            ).get()
            item["extras"]["check_date"] = location["updated_at"]

            yield item
