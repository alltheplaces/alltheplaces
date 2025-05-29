from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class GscaltexKRSpider(Spider):
    name = "gscaltex_kr"
    item_attributes = {"brand_wikidata": "Q624012"}
    start_urls = ["https://www.gscenergyplus.com/data/station/map.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["siteList"]:
            item = Feature()
            item["ref"] = location["siteCd"]
            item["phone"] = location["telNo"]
            item["postcode"] = location["zipNo"]
            item["street_address"] = location["detAddr"]
            item["lat"] = location["lat"]
            item["lon"] = location["longi"]

            apply_yes_no(Extras.CAR_WASH, item, location["carWashYn"] == "Y")
            apply_category(Categories.FUEL_STATION, item)

            # TODO: location["siteSxnCd"]

            yield item
