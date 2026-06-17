import json
import re

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HiUSSpider(StructuredDataSpider):
    name = "hi_us"
    item_attributes = {
        "brand": "Hostelling International",
        "brand_wikidata": "Q16980401",
        "country": "US",
    }
    # All hostels are listed in a JSON blob on the find-a-hostel page
    start_urls = ["https://www.hiusa.org/find-hostels"]
    wanted_types = ["Hotel"]
    search_for_twitter = False
    drop_attributes = {"image"}

    def parse(self, response: Response, **kwargs):
        # Extract the hostel list from the data-hostels JSON attribute
        raw = response.css("span#site-hostels-list::attr(data-hostels)").get()
        if not raw:
            return
        data = json.loads(raw.replace("&quot;", '"'))
        for hostel in data.get("hostels", []):
            yield response.follow(hostel["hostel_url"], callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # The JSON-LD Hotel type has full address but no coordinates.
        # Coordinates appear in a Google Maps directions link: destination=lat,lon
        maps_href = response.css("a.hostel-details__address::attr(href)").get("")
        coords_match = re.search(r"destination=(-?\d+\.?\d*),(-?\d+\.?\d*)", maps_href)
        if coords_match:
            item["lat"] = float(coords_match.group(1))
            item["lon"] = float(coords_match.group(2))
        else:
            return  # skip items without coordinates

        # Use URL slug as stable ref
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url

        # Per-location name → branch
        item["branch"] = item.pop("name", None)

        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
