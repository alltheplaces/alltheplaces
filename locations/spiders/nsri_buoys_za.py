from typing import Any

from chompjs import parse_js_object
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature


class NsriBuoysZASpider(Spider):
    name = "nsri_buoys_za"
    item_attributes = {
        "operator": "National Sea Rescue Institute",
        "operator_wikidata": "Q6978306",
        "extras": Categories.RESCUE_BUOY.value,
    }
    start_urls = ["https://www.nsri.org.za/water-safety/pink-rescue-buoys"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data_raw = response.xpath('.//script[contains(text(), "window._gmData.infoWindows")]/text()').get()
        locations = parse_js_object(data_raw.split("['buoy-finder']")[1])

        for location in locations.values():
            selector = Selector(text=location["content"])
            item = Feature()
            item["ref"] = selector.xpath("//h3/text()").get().removeprefix("-").strip()

            coordinates = selector.xpath("//p/text()").get().split(",")
            item["lat"] = coordinates[0]
            item["lon"] = coordinates[1]

            yield item
