import re
from typing import Iterable

import chompjs
from scrapy.http import Response, TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AuntieAnnesGBSpider(JSONBlobSpider):
    name = "auntie_annes_gb"
    item_attributes = {"brand": "Auntie Anne's", "brand_wikidata": "Q4822010"}
    start_urls = ["https://www.auntieannes.co.uk/locations/"]
    drop_attributes = {"facebook", "twitter"}

    def extract_json(self, response: Response) -> dict | list[dict]:
        return chompjs.parse_js_object(
            re.search(
                r'"objects":(\[.+?]),"schema"',
                response.xpath("//script[contains(text(), 'mapsvg_options')]/text()").get(),
            ).group(1)
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature["location"]["address"]["formatted"]
        if feature["location"]["address"].get("postal_town"):
            item["city"] = feature["location"]["address"]["postal_town"]
        else:
            item["city"] = feature["location"]["address"]["locality"]
        item["lat"], item["lon"] = feature["location"]["geoPoint"]["lat"], feature["location"]["geoPoint"]["lng"]
        item["branch"] = item.pop("name")
        item["country"] = feature["location"]["address"]["country"]
        item["opening_hours"] = OpeningHours()
        time = str(feature["opening_hours"])
        time = re.sub("<[^<]+?>", "", time)
        item["opening_hours"].add_ranges_from_string(time)
        yield item
