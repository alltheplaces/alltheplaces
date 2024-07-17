import re
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

ACCESS_MAP = {
    "brown": "private",
    "yellow": "customers",
    "blue": "yes",
}


class BreakAndWashPLSpider(Spider):
    name = "break_and_wash_pl"
    item_attributes = {"name": "Break & Wash", "brand": "Break & Wash", "brand_wikidata": "Q125499503"}
    start_urls = ["https://breakandwash.pl/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for ref, lat, lon, content, colour in re.findall(
            r"window\.locations\.push\({\s+id: 'location_id_(\d+)',\s+lat: '([\-\d \.]+)',\s+lng: '([\-\d \.]+)',\s+content: '(.+?)',\s+color: '(.+?)'\s+}\);",
            response.text,
        ):
            item = Feature()
            item["ref"] = ref
            item["lat"] = lat
            item["lon"] = lon
            html = Selector(text=content)
            item["branch"] = html.xpath("//h5/text()").get()
            item["addr_full"] = merge_address_lines(html.xpath("//p/text()").getall())

            item["extras"]["access"] = ACCESS_MAP.get(colour)

            apply_category({"amenity": "vending_machine", "vending": "laundry"}, item)

            yield item
