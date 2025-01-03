from html import unescape

from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GoodyearAutocareAUNZSpider(Spider):
    name = "goodyear_autocare_au_nz"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    allowed_domains = ["www.goodyearautocare.com.au", "www.goodyear.co.nz"]
    start_urls = [
        "https://www.goodyearautocare.com.au/slocator/json/search/",
        "https://www.goodyear.co.nz/slocator/json/search/",
    ]

    @staticmethod
    def request_page(url: str, page_number: int) -> FormRequest:
        formdata = {
            "address": "null",
            "latitude": "null",
            "longitude": "null",
            "page": str(page_number),
        }
        return FormRequest(url=url, formdata=formdata, meta={"page": page_number}, method="POST", dont_filter=True)

    def start_requests(self):
        for url in self.start_urls:
            yield self.request_page(url, 1)

    def parse(self, response):
        for location in response.json()["maps"]["items"]:
            if location["is_active"] != "1":
                continue
            if not location["url"].startswith("goodyear-autocare-"):
                continue
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Goodyear Autocare ")
            item["ref"] = location["entity_id"]
            item["street_address"] = unescape(item.pop("street"))
            item["country"] = location["country_id"]
            item["website"] = "https://www.goodyearautocare.com.au/store-locator/" + location["url"]
            item["opening_hours"] = OpeningHours()
            hours_string = ""
            if location["mon_fri_open"] and location["mon_fri_close"]:
                hours_string = f"{hours_string} Mon-Fri: " + location["mon_fri_open"] + "-" + location["mon_fri_close"]
            for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sunday"]:
                if not location[f"{day}_open"] or not location[f"{day}_close"]:
                    continue
                if "Appointment" in location[f"{day}_open"].title():
                    continue
                hours_string = (
                    f"{hours_string} {day.title()}: " + location[f"{day}_open"] + "-" + location[f"{day}_close"]
                )
            item["opening_hours"].add_ranges_from_string(hours_string)
            apply_yes_no(Extras.WIFI, item, location["guest_wifi"] == "1", False)
            apply_yes_no(Extras.WHEELCHAIR, item, location["wheelchair_access"] == "1", False)
            apply_yes_no(Extras.INDOOR_SEATING, item, location["waiting_area"] == "1", False)
            yield item

        if response.json()["stopLoad"]:
            return

        yield self.request_page(response.url, response.meta["page"] + 1)
