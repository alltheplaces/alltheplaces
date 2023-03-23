import collections

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class Brico_ioITSpider(Spider):
    name = "brico_io_it"
    item_attributes = {"brand": "Brico io", "brand_wikidata": "Q15965705"}
    allowed_domains = ["www.bricoio.it"]
    start_urls = ["https://www.bricoio.it/it/it/brit/storelocator/getallstores"]

    def parse(self, response):
        for location in response.json():
            if not location["isActive"]:
                continue

            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["name"] = location["alias"]
            address_fields = {k: v for k, v in DictParser.parse(location["address"]).items() if v}
            print(address_fields)
            item["street_address"] = " ".join(
                filter(None, [location["address"]["street1"], location["address"]["street2"]])
            )
            item.update(address_fields)
            for contact_method in location["contacts"]:
                if contact_method["type"] == 1:
                    item["email"] = contact_method["destination"]
                if contact_method["type"] == 3:
                    item["phone"] = contact_method["destination"]
            item["website"] = "https://www.bricoio.it/it/it/brit/storelocator/store/" + item["ref"]

            day_list = collections.deque(DAYS.copy())
            day_list.rotate(1)
            item["opening_hours"] = OpeningHours()
            for timeslot in location["hours"]["timeslots"]:
                open_time = str(timeslot["from"]["hours"]) + ":" + str(timeslot["from"]["minutes"]).zfill(2)
                close_time = str(timeslot["to"]["hours"]) + ":" + str(timeslot["to"]["minutes"]).zfill(2)
                item["opening_hours"].add_range(day_list[timeslot["dayOfWeek"]], open_time, close_time)

            yield item
