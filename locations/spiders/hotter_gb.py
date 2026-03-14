from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class HotterGBSpider(JSONBlobSpider):
    name = "hotter_gb"
    item_attributes = {"brand": "Hotter", "brand_wikidata": "Q91919346"}
    start_urls = [
        "https://storelocator.hotter.com/wp-admin/admin-ajax.php?action=store_search&lat=53.53054&lng=-2.75425&max_results=250&search_radius=25&filter=4&autoload=1"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "storelocator.hotter.com",
            "Alt-Used": "storelocator.hotter.com",
        },
    }
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["store"]
        apply_category(Categories.SHOP_SHOES, item)
        item["street_address"] = item.pop("addr_full", None)
        yield item
