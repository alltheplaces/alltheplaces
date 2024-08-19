from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BwsAUSpider(Spider):
    name = "bws_au"
    item_attributes = {"brand": "BWS", "brand_wikidata": "Q4836848", "extras": Categories.SHOP_ALCOHOL.value}
    allowed_domains = ["api.bws.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "AU"

    def start_requests(self) -> Iterable[Request]:
        for state in ["ACT", "NSW", "QLD", "SA", "VIC", "TAS", "WA", "NT"]:
            yield JsonRequest(
                "https://api.bws.com.au/apis/ui/StoreLocator/Stores/bws?state={}&type=allstores&Max=5000".format(state)
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["StoreNo"]
            if branch_name := item.pop("name", None):
                item["branch"] = branch_name
            slug = "{}-{}-{}".format(location["State"], location["Suburb"].replace(" ", "-"), item["ref"])
            item["website"] = urljoin("https://bws.com.au/storelocator/", slug.lower())

            day_hours_strings = []
            for day_hours in location.get("TradingHours", []):
                day_hours_strings.append(day_hours["Day"] + ": " + day_hours["OpenHour"])
            hours_string = " ".join(day_hours_strings)
            day_pairs = [
                ["Monday", "Tuesday"],
                ["Tuesday", "Wednesday"],
                ["Wednesday", "Thursday"],
                ["Thursday", "Friday"],
                ["Friday", "Saturday"],
                ["Saturday", "Sunday"],
                ["Sunday", "Monday"],
            ]
            for day_pair in day_pairs:
                if day_pair[0] not in hours_string and day_pair[1] not in hours_string:
                    hours_string = hours_string.replace("Today", day_pair[0]).replace("Tomorrow", day_pair[1])
                    break
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
