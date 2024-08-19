from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class DanMurphysAUSpider(Spider):
    name = "dan_murphys_au"
    item_attributes = {"brand": "Dan Murphy's", "brand_wikidata": "Q5214075", "extras": Categories.SHOP_ALCOHOL.value}
    allowed_domains = ["api.danmurphys.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def start_requests(self) -> Iterable[Request]:
        for state in ["ACT", "NSW", "QLD", "SA", "VIC", "TAS", "WA", "NT"]:
            yield JsonRequest(
                "https://api.danmurphys.com.au/apis/ui/StoreLocator/Stores/bws?state={}&type=allstores&Max=5000".format(
                    state
                )
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["Id"]
            if branch_name := item.pop("name", None):
                item["branch"] = branch_name
            item["street_address"] = merge_address_lines([location["AddressLine1"], location["AddressLine2"]])
            slug = "{}-{}-{}".format(location["State"], location["Suburb"].replace(" ", "-"), item["ref"])
            item["website"] = urljoin("https://danmurphys.com.au/stores/", slug)

            item["opening_hours"] = OpeningHours()
            for rule in location["OpeningHours"]:
                item["opening_hours"].add_range(rule["Day"], *rule["Hours"].split(" - "), "%I:%M %p")

            yield item
