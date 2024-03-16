from scrapy import FormRequest, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

COUNTRY_MAP = {101: "Botswana", 155: "Lesotho", 182: "Namibia", 73: "South Africa", 219: "Swaziland"}


def add_times(opening_hours: OpeningHours, day, times):
    if not times:
        return
    start_time, end_time = times.split(" - ")
    if isinstance(day, list):
        opening_hours.add_days_range(day, start_time, end_time, time_format="%I:%M%p")
    else:
        opening_hours.add_range(day, start_time, end_time, time_format="%I:%M%p")


class LewisStoresSpider(Spider):
    name = "lewis_stores"
    item_attributes = {"brand": "Lewis Stores", "brand_wikidata": "Q116474928"}

    def start_requests(self):
        yield FormRequest(
            url="https://lewisstores.co.za/controllers/get_locations.php", formdata={"param1": "Lewis Stores"}
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            for k, v in location.items():
                if v == "NULL":
                    location[k] = None

            location["country"] = COUNTRY_MAP.get(location["CountryId"])
            location["street_address"] = (
                location.pop("Address").replace(location["City"], "").replace(location["country"], "")
            )
            location["phone"] = "; ".join(filter(None, [location.pop("Phone"), location["Phone2"], location["Phone3"]]))
            location["name"] = location["StoreLocatorName"]

            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            add_times(item["opening_hours"], DAYS[0:5], location["TradingMonFri"])
            add_times(item["opening_hours"], "Sa", location["TradingSat"])
            add_times(item["opening_hours"], "Su", location["TradingSunPub"])

            yield item
