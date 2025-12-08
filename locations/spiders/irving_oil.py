from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class IrvingOilSpider(Spider):
    name = "irving_oil"
    start_urls = ["https://www.irvingoil.com/location/geojson"]
    item_attributes = {"brand": "Irving", "brand_wikidata": "Q1673286"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["features"]:
            props = location["properties"]
            if props["isBigStop"]:
                continue

            item = Feature()
            item["ref"] = props["nid"]
            item["geometry"] = location["geometry"]
            item["website"] = response.urljoin(props["link"])
            item["addr_full"] = merge_address_lines(Selector(text=props["address"]).xpath("//text()").getall())
            item["phone"] = props["phone"]

            apply_yes_no(Extras.SHOWERS, item, props["showers"])
            apply_yes_no(Extras.CAR_WASH, item, props["carWash"])
            apply_yes_no(Fuel.DIESEL, item, props["diesel"])

            apply_category(Categories.FUEL_STATION, item)

            yield item
