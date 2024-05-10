from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BricoIOITSpider(Spider):
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
            item["street_address"] = clean_address([location["address"]["street1"], location["address"]["street2"]])
            item["country"] = location["address"]["idCountry"]
            for contact_method in location["contacts"]:
                if contact_method["type"] == 1:
                    item["email"] = contact_method["destination"]
                if contact_method["type"] == 3:
                    item["phone"] = contact_method["destination"]
            item["website"] = "https://www.bricoio.it/it/it/brit/storelocator/store/" + item["ref"]

            item["opening_hours"] = OpeningHours()
            for timeslot in location["hours"]["timeslots"]:
                item["opening_hours"].add_range(
                    DAYS[timeslot["dayOfWeek"] - 1], timeslot["from"], timeslot["to"], "%H:%M:%S"
                )

            yield item
