import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class ExtendedStayAmericaSpider(Spider):
    name = "extended_stay_america"
    item_attributes = {
        "brand": "Extended Stay America",
        "brand_wikidata": "Q5421850",
        "country": "US",
    }
    start_urls = ["https://www.extendedstayamerica.com/hotels"]
    custom_settings = {"AUTOTHROTTLE_ENABLED": True, "USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(re.search(r"hotelsData\s*=\s*(\[.*\]);", response.text).group(1))
        for location in raw_data:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location["siteId"]
            item["website"] = response.urljoin(location["urlMap"])
            # DictParser maps "street" -> addr:street (street name only), but the source
            # field contains the full address line including house number, so use street_address.
            if street := item.pop("street", None):
                item["street_address"] = street
            yield item
