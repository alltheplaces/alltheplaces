import scrapy
from scrapy import FormRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class OlliesBargainOutletSpider(scrapy.Spider):
    name = "ollies_bargain_outlet"
    allowed_domains = ["ollies.us"]
    item_attributes = {"brand": "Ollie's Bargain Outlet", "brand_wikidata": "Q7088304"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "US"

    def start_requests(self):
        formdata = {
            "Page": "0",
            "PageSize": "1",
            "StartIndex": "0",
            "EndIndex": "5",
            "Longitude": "-74.006065",
            "Latitude": "40.712792",
            "City": "",
            "State": "",
            "F": "GetNearestLocations",
            "RangeInMiles": "5000",
        }
        url = "https://www.ollies.us/admin/locations/ajax.aspx"
        headers = {"content-type": "application/x-www-form-urlencoded; charset=UTF-8"}

        yield FormRequest(url=url, method="POST", headers=headers, formdata=formdata, callback=self.get_all_locations)

    def get_all_locations(self, response):
        number_locations = response.json().get("LocationsCount")
        formdata = {
            "Page": "0",
            "PageSize": str(number_locations),
            "StartIndex": "0",
            "EndIndex": "5",
            "Longitude": "-74.006065",
            "Latitude": "40.712792",
            "City": "",
            "State": "",
            "F": "GetNearestLocations",
            "RangeInMiles": "5000",
        }
        url = "https://www.ollies.us/admin/locations/ajax.aspx"
        headers = {"content-type": "application/x-www-form-urlencoded; charset=UTF-8"}

        yield FormRequest(url=url, method="POST", headers=headers, formdata=formdata, callback=self.parse)

    def parse(self, response):
        for data in response.json().get("Locations"):
            item = DictParser.parse(data)
            item["ref"] = data.get("StoreCode")
            item["country"] = "US"
            item["website"] = f'https://www.{self.allowed_domains[0]}{data.get("CustomUrl")}'
            item["ref"] = data.get("StoreCode")

            open_hours = data.get("OpenHours").split("<br />")
            open_hour_filtered = [row.replace(":", "") for row in open_hours if "-" in row]
            oh = OpeningHours()
            oh.from_linked_data({"openingHours": open_hour_filtered}, "%I%p")
            item["opening_hours"] = oh.as_opening_hours()

            yield item
