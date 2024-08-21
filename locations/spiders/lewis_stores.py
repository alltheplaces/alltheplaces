import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours


class LewisStoresSpider(scrapy.Spider):
    name = "lewis_stores"
    item_attributes = {"brand": "Lewis Stores", "brand_wikidata": "Q115117217"}

    def start_requests(self):
        yield scrapy.http.FormRequest(
            url="https://lewisstores.co.za/controllers/get_locations.php",
            formdata={"param1": "Lewis Stores"},
        )

    def parse(self, response):
        for location in response.json():
            if "CLOSED" in location["StoreLocatorName"]:
                continue

            location["Phone"] = "; ".join([location["Phone"], location.pop("Phone2"), location.pop("Phone3")])

            item = DictParser.parse(location)
            country_code_mapping = {
                182: "NA",
                73: "ZA",
                219: "SZ",
                155: "LS",
                101: "BW",
            }
            item["branch"] = location["StoreLocatorName"]
            item["email"] = item["email"].replace("NULL", "")
            item["country"] = country_code_mapping[location["CountryId"]]

            if item["country"] != "ZA" and item["postcode"] in ["9000", "9999"]:
                item.pop("postcode")

            oh = OpeningHours()
            time_format = "%I:%M%p" if "am" in location["TradingMonFri"] else "%H:%M"
            if location["TradingMonFri"] == "CLOSED":
                oh.set_closed(DAYS_WEEKDAY)
            else:
                for day in DAYS_WEEKDAY:
                    oh.add_range(
                        day,
                        location["TradingMonFri"].split("-")[0].strip(),
                        location["TradingMonFri"].split("-")[1].strip(),
                        time_format=time_format,
                    )
            if location["TradingSat"] == "CLOSED":
                oh.set_closed("Sat")
            else:
                oh.add_range(
                    "Sat",
                    location["TradingSat"].split("-")[0].strip(),
                    location["TradingSat"].split("-")[1].strip(),
                    time_format=time_format,
                )
            if location["TradingSunPub"] == "CLOSED":
                oh.set_closed("Sun")
            else:
                oh.add_range(
                    "Sun",
                    location["TradingSunPub"].split("-")[0].strip(),
                    location["TradingSunPub"].split("-")[1].strip(),
                    time_format=time_format,
                )

            item["opening_hours"] = oh

            yield item
