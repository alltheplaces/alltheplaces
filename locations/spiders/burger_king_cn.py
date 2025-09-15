import re
from typing import Any, Iterable

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCNSpider(JSONBlobSpider):
    name = "burger_king_cn"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    locations_key = ["data", "data"]

    def start_requests(self) -> Iterable[Request]:
        yield Request(url="https://www.bkchina.cn/website/new/js/area.js", callback=self.parse_regions)

    def parse_regions(self, response: Response) -> Any:
        provinces_list = []
        provinces = {}
        for code, line in re.findall(r"dsy\.add\(\"(\w+)\",(\[.+?])\)", response.text, re.DOTALL):
            areas = parse_js_object(line)
            if "_" not in code and provinces == {}:
                provinces_list = areas
                provinces = {province: [] for province in areas}
            elif len(code.split("_")) == 2:
                provinces[provinces_list[int(code.split("_")[1])]] = areas
        for province, cities in provinces.items():
            for city in cities:
                yield from self.request_page(province, city, 1)

    def request_page(self, province: str, city: str, page: int) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url=f"https://www.bkchina.cn/restaurant/getMapsListAjax?page={page}&storeProvince={province}&storeCity={city}&localSelect=&search=",
            meta={
                "province": province,
                "city": city,
                "page": page,
            },
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        if int(response.json()["data"]["total"]) == 0:
            self.logger.debug(
                f"No stores found for province: {response.meta['province']}, city: {response.meta['city']}"
            )
            return
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features) or []
        if int(response.json()["data"]["total"]) > 5 * response.meta["page"]:
            yield from self.request_page(response.meta["province"], response.meta["city"], response.meta["page"] + 1)

    def pre_process_data(self, feature: dict) -> None:
        # Lat and long are the wrong way round
        feature["latitude"] = feature.pop("storeLongitude")
        feature["longitude"] = feature.pop("storeLatitude")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["state"] = feature["storeProvince"]
        apply_yes_no(Extras.BREAKFAST, item, feature["hasBreakfast"] == "1", False)
        item["brand"] = "汉堡王"
        yield item
