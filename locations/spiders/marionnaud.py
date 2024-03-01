from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class MarionnaudSpider(Spider):
    name = "marionnaud"
    item_attributes = {"brand": "Marionnaud", "brand_wikidata": "Q1129073"}
    start_urls = [
        "https://www.marionnaud.at/api/v2/mat/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://www.marionnaud.ch/api/v2/mch/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://www.marionnaud.cz/api/v2/mcz/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://www.marionnaud.hu/api/v2/mhu/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://www.marionnaud.it/api/v2/mit/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://www.marionnaud.ro/api/v2/mro/stores?radius=10000&pageSize=100000&fields=FULL",
        "https://www.marionnaud.sk/api/v2/msk/stores?radius=10000&pageSize=100000&fields=FULL",
        # fr
    ]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}
    requires_proxy = True

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["addr_full"] = location["formattedAddress"]
            item["street_address"] = merge_address_lines([location["line1"], location.get("line2")])
            item["website"] = response.urljoin(location["url"])

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]["weekDayOpeningList"]:
                if rule["closed"]:
                    continue
                item["opening_hours"].add_range(
                    rule["shortenedWeekDay"],
                    rule["openingTime"]["formattedHour"].replace(".", ":"),
                    rule["closingTime"]["formattedHour"].replace(".", ":"),
                )
            # item["country"] = None
            yield item
