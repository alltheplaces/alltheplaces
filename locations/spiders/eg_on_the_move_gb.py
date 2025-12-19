from typing import Any
from urllib.parse import quote

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class EgOnTheMoveGBSpider(Spider):
    name = "eg_on_the_move_gb"
    item_attributes = {"brand": "EG On the Move", "brand_wikidata": "Q130223576"}
    start_urls = ["https://eg-otm.com/api/sites"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            brands = location["Brands"].split(", ")
            if not ("EGOTM" in brands and "PFS" in brands):
                continue

            item = Feature()
            item["ref"] = location["SiteCode"]
            item["branch"] = location["SiteName"]
            item["city"] = location["City"]
            item["country"] = location["Country"]
            item["lat"] = location["SiteLatitude"]
            item["lon"] = location["SiteLongitude"]
            item["addr_full"] = location["FullAddress"]
            item["state"] = location["Region"]
            item["website"] = "https://eg-otm.com/locations/{}/{}".format(quote(location["City"]), location["SiteCode"])

            apply_category(Categories.FUEL_STATION, item)

            yield item
