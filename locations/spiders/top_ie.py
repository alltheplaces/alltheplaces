from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class TopIESpider(Spider):
    name = "top_ie"
    item_attributes = {"brand": "Top", "brand_wikidata": "Q7693933"}
    start_urls = ["https://www.top.ie/top_location_finder/locations/station"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location["properties"])
            item["ref"] = location["properties"]["nid"]
            item["website"] = response.urljoin(location["properties"]["link"])

            apply_yes_no(Extras.ATM, item, location["properties"]["hasAtm"] is True)
            apply_yes_no(Extras.ATM, item, location["properties"]["hasToilets"] is True)
            apply_yes_no(Access.HGV, item, location["properties"]["hasHGV"] is True)
            apply_yes_no(Fuel.ADBLUE, item, location["properties"]["hasAdBlue"] is True)
            apply_yes_no(Fuel.KEROSENE, item, location["properties"]["hasKerosenePump"] is True)

            if location["properties"]["isOpen24Hours"] is True:
                item["opening_hours"] = "24/7"

            apply_category(Categories.FUEL_STATION, item)

            yield item
