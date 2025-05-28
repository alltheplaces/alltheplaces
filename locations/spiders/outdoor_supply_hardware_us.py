import json
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


def decode_email(s):
    s = bytes.fromhex(s)
    return "".join(chr(c ^ s[0]) for c in s[1:])


class OutdoorSupplyHardwareUSSpider(Spider):
    name = "outdoor_supply_hardware_us"
    item_attributes = {"brand": "Outdoor Supply Hardware", "brand_wikidata": "Q119104427"}
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "RETRY_HTTP_CODES": [403],  # Sometimes server blocks and sometimes allows
        "RETRY_TIMES": 5,
    }
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            url="https://www.outdoorsupplyhardware.com/Locations",
            headers={
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        root = response.xpath('//*[@id="hiddenLocationData"]')[0].root

        for el in root:
            el.text = decode_email(el.get("data-cfemail"))

        for location in json.loads(root.text_content()):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street", None)
            item["extras"]["fax"] = location["faxNum"]

            hours = OpeningHours()
            for line in location["workHour"][len("<p>") : -len("</p>")].split("</br>"):
                hours.add_ranges_from_string(line)
            item["opening_hours"] = hours

            yield item
