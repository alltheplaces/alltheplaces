from typing import Any

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class ManhattanBagelSpider(Spider):
    """Copy of Einstein Bros. Bagels - all brands of the same parent company Coffee & Bagels"""

    name = "manhattan_bagel"
    item_attributes = {"brand": "Manhattan Bagel", "brand_wikidata": "Q64517333"}

    def start_requests(self):
        url = "https://www.manhattanbagel.com/wp-admin/admin-ajax.php"

        form_data = {
            "action": "get_initial_location_results_for_map_markers",
            "max_results": "100",
        }

        yield FormRequest(
            url=url,
            method="POST",
            formdata=form_data,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = location["location_street"]
            item["city"] = location["location_city"]
            item["postcode"] = location["location_zipcode"]
            item["website"] = location["location_link"]
            item["phone"] = location["location_phone"]
            yield item
