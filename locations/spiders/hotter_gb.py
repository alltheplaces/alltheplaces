from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class HotterGBSpider(JSONBlobSpider):
    name = "hotter_gb"
    item_attributes = {"brand": "Hotter", "brand_wikidata": "Q91919346"}
    start_urls = ["https://storelocator.hotter.com/wp-admin/admin-ajax.php?action=store_search&lat=53.53054&lng=-2.75425&max_results=250&search_radius=25&filter=4&autoload=1"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False,
       "DEFAULT_REQUEST_HEADERS": {
            "Host": "storelocator.hotter.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
            "Alt-Used": "storelocator.hotter.com",
        }
    }
