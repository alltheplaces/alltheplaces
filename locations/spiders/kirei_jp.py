import re
from typing import Any

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class KireiJPSpider(Spider):
    name = "kirei_jp"

    start_urls = [
        "https://www.dnpphoto.jp/CGI/api/search/list.cgi?lat=36&lon=138&search_lat_A=0&search_lon_A=0&search_lat_B=90&search_lon_B=180"
    ]
    item_attributes = {"brand_wikidata": "Q11196102", "brand": "Ki-Re-i"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        transformer = Transformer.from_pipeline("EPSG:15484")
        for store in response.json()["list"]:

            item = Feature()

            item["branch"] = store.get("place")
            item["lat"], item["lon"] = transformer.transform(store.get("lat"), store.get("lon"))
            item["addr_full"] = store.get("add")
            item["website"] = f"https://www.dnpphoto.jp/CGI/search/detail.cgi?seq={store.get('seq')}"
            item["ref"] = store.get("seq")
            apply_category(Categories.PHOTO_BOOTH, item)

            yield Request(item["website"], self.parse_details, cb_kwargs={"item": item})

    def parse_details(self, response: Response, item: Feature) -> Any:
        hours = response.xpath('//th[text()="営業時間"]/following-sibling::td/text()').get("")
        oh = OpeningHours()
        if "24時間" in hours:
            oh.add_days_range(DAYS, "00:00", "23:59")
        elif m := re.search(r"(\d+)[:：](\d+)\s*[～~]\s*(\d+)[:：](\d+)", hours):
            oh.add_days_range(DAYS, f"{m[1]}:{m[2]}", f"{m[3]}:{m[4]}")
        item["opening_hours"] = oh
        yield item
