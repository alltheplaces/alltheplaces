import json
from typing import Iterable

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


def decode_email(s):
    s = bytes.fromhex(s)
    return "".join(chr(c ^ s[0]) for c in s[1:])


class OutdoorSupplyHardwareUSSpider(Spider):
    name = "outdoor_supply_hardware_us"
    item_attributes = {"brand": "Outdoor Supply Hardware", "brand_wikidata": "Q119104427"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            url="https://www.outdoorsupplyhardware.com/Locations",
            headers={
                "sec-fetch-site": "same-origin",
            },
        )

    def parse(self, response, **kwargs):
        root = response.xpath('//*[@id="hiddenLocationData"]')[0].root

        for el in root:
            el.text = decode_email(el.get("data-cfemail"))

        for location in json.loads(root.text_content()):
            item = DictParser.parse(location)
            del item["street"]

            item["branch"] = location["branchName"]
            item["ref"] = location["branchId"]
            item["street_address"] = location["street"]
            item["extras"]["fax"] = location["faxNum"]

            hours = OpeningHours()
            for line in location["workHour"][len("<p>") : -len("</p>")].split("</br>"):
                hours.add_ranges_from_string(line)
            item["opening_hours"] = hours.as_opening_hours()

            yield item
