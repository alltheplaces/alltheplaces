from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class PatheNLSpider(Spider):
    name = "pathe_nl"
    item_attributes = {"brand": "Pathé", "brand_wikidata": "Q3060526"}
    start_urls = ["https://www.pathe.nl/api/cinemas"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}  # the API returns HTTP 403 to non-browser user agents
    requires_proxy = "NL"  # Akamai also blocks data-centre IPs (CI fetch gets HTTP 403); needs a NL proxy

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for cinema in response.json():
            if not cinema["status"]:
                continue
            for theater in cinema["theaters"]:
                item = DictParser.parse(theater)  # maps name, addressLine1 (-> street_address), city, postcode
                item["ref"] = cinema["slug"]
                item["lat"] = theater["gpsPosition"]["x"]
                item["lon"] = theater["gpsPosition"]["y"]
                item["website"] = "https://www.pathe.nl/nl/bioscopen/{}".format(cinema["slug"])
                apply_category(Categories.CINEMA, item)
                yield item
