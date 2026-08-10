from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Access, Categories, apply_category, apply_yes_no
from locations.items import Feature


class GvTruckBESpider(Spider):
    name = "gv_truck_be"
    item_attributes = {"name": "G&V Truck", "brand": "G&V Truck"}
    start_urls = ["https://www.gvtruck.be/en/network"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "locations")]/text()').re_first(r"\"locations\":(\[.+?\])")
        ):
            if "Pin-Train" in location["marker"]:
                continue
            item = Feature()
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]

            sel = Selector(text=location["balloon"])
            item["branch"] = sel.xpath("//span/text()").get().removeprefix("G&V Truck ")
            item["addr_full"] = sel.xpath("//p[2]/text()").getall()
            item["website"] = item["ref"] = response.urljoin(sel.xpath("//a/@href").get())

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Access.HGV, item, True)

            yield item
