from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HuhotMongolianGrillUSSpider(StructuredDataSpider):
    name = "huhot_mongolian_grill_us"
    item_attributes = {"brand": "HuHot", "brand_wikidata": "Q5924606", "name": "HuHot"}
    start_urls = ["https://www.huhot.com/locations/"]
    wanted_types = ["Restaurant"]
    time_format = "%H:%M:%S"
    search_for_image = False

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for marker in response.css("a.marker"):
            lat, lon = marker.attrib["data-latlng"].split(",")
            yield Request(marker.attrib["href"], callback=self.parse_sd, meta={"lat": lat, "lon": lon})

    def post_process_item(self, item, response, ld_data, **kwargs) -> Iterable[Any]:
        item["lat"] = response.meta["lat"]
        item["lon"] = response.meta["lon"]
        item["branch"] = response.css("h1.sr-only::text").get()
        item.pop("name", None)  # the site's "name" is just "HuHot - <city>, <state>"; use item_attributes instead
        item["image"] = None  # the same handful of generic stock photos are reused across unrelated locations
        apply_category(Categories.RESTAURANT, item)
        yield item
