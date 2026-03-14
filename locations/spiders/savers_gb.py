from typing import Any
from urllib.parse import urljoin

import xmltodict
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class SaversGBSpider(Spider):
    name = "savers_gb"
    item_attributes = {"brand": "Savers", "brand_wikidata": "Q7428189"}
    start_urls = ["https://api.savers.co.uk/api/v2/sv/stores?country=GB&currentPage=0&pageSize=1000"]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in xmltodict.parse(response.text)["storeFinderSearchPage"]["stores"]:
            location.update(location.pop("address"))
            location.update(location.pop("geoPoint"))
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["branch"] = location["displayName"]
            item["street_address"] = merge_address_lines([location.get("line2"), location.get("line1")])
            item["website"] = urljoin("https://www.savers.co.uk", location["url"])
            item["opening_hours"] = OpeningHours()
            for day_time in location["openingHours"]["weekDayOpeningList"]:
                day = day_time["weekDay"]
                open_time = day_time["openingTime"]["formattedHour"]
                close_time = day_time["closingTime"]["formattedHour"]
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item
