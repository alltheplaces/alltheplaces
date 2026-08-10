from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KireiJPSpider(Spider):
    name = "kirei_jp"

    start_urls = [
        "https://www.dnpphoto.jp/CGI/api/search/list.cgi?lat=36&lon=138&search_lat_A=0&search_lon_A=0&search_lat_B=90&search_lon_B=180"
    ]
    item_attributes = {"brand_wikidata": "Q11196102", "brand": "Ki-Re-i"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["list"]:

            item = Feature()

            item["branch"] = store.get("place")
            item["lat"] = store.get("lat")
            item["lon"] = store.get("lon")
            item["addr_full"] = store.get("add")
            item["website"] = f"https://www.dnpphoto.jp/CGI/search/detail.cgi?seq={store.get('seq')}"
            item["ref"] = store.get("seq")
            apply_category(Categories.PHOTO_BOOTH, item)

            yield item
