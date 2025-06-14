from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class PopeyesGBSpider(Spider):
    name = "popeyes_gb"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}

    start_urls = ["https://pe-uk-ordering-api-fd-eecsdkg6btfeg0cc.z01.azurefd.net/api/v2/restaurants"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["lat"] = location["storeLocation"]["coordinates"]["latitude"]
            item["lon"] = location["storeLocation"]["coordinates"]["longitude"]
            item["branch"] = item.pop("name")
            item["website"] = urljoin("https://popeyesuk.com/restaurants/", location["slug"])

            apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"] is True)
            apply_yes_no(Extras.TOILETS, item, location["hasToilets"] is True or location["hasDisabledToilets"] is True)
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, location["hasDisabledToilets"] is True)
            apply_yes_no(Extras.WHEELCHAIR, item, location["hasDisabledAccess"] is True)
            apply_yes_no(Extras.WIFI, item, location["hasWiFi"] is True)
            yield item
