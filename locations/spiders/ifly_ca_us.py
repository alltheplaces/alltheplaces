from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class iFLYCAUSSpider(Spider):
    name = "ifly_ca_us"
    item_attributes = {"brand": "iFLY", "brand_wikidata": "Q64767105"}
    allowed_domains = ["dataanywhereprod.azure-api.net"]
    start_urls = ["https://dataanywhereprod.azure-api.net/SL/V2/api/stores/"]

    def start_requests(self):
        headers = {
            "Referer": "https://www.iflyworld.com/",
            "ocp-apim-subscription-key": "d8c538d6a8de45398f6f1d4a6405102f",
            "Origin": "https://www.iflyworld.com",
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, headers=headers)

    def parse(self, response):
        for location in response.json()["StoreLocations"]:
            item = DictParser.parse(location)
            item["ref"] = location["ExtraData"]["ReferenceCode"]
            item["geometry"] = location["Location"]
            item["street_address"] = clean_address(
                [
                    location["ExtraData"]["Address"].get("AddressNonStruct_Line1"),
                    location["ExtraData"]["Address"].get("AddressNonStruct_Line2"),
                ]
            )
            item["city"] = location["ExtraData"]["Address"].get("Locality")
            item["state"] = location["ExtraData"]["Address"].get("Region")
            item["postcode"] = location["ExtraData"]["Address"].get("PostalCode")
            item["country"] = location["ExtraData"]["Address"].get("CountryCode")
            item["phone"] = location["ExtraData"].get("Phone")
            item["opening_hours"] = OpeningHours()
            for day_abbrev, hours_ranges in location["ExtraData"]["HoursOfOpStruct"].items():
                if day_abbrev == "SpecialHours" or not hours_ranges.get("Ranges"):
                    continue
                for hours_range in hours_ranges["Ranges"]:
                    item["opening_hours"].add_range(
                        day_abbrev.title(), hours_range["StartTime"], hours_range["EndTime"], "%I:%M%p"
                    )
            yield item
