from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class MinisoGBSpider(JSONBlobSpider):
    name = "miniso_gb"
    item_attributes = {"brand": "Miniso", "brand_wikidata": "Q20732498"}
    start_urls = ["https://minisoshop.co.uk/psstore-locator/ajax/search/?q=&is_region=0&view_all=1&_=1785238195920"]
    requires_proxy = "GB"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "x-requested-with": "XMLHttpRequest",
        },
    }
    locations_key = "items"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([item.pop("addr_full"), feature.get("address_line_2")])
        item["branch"] = item.pop("name").replace("MINISO ", "")
        yield item
