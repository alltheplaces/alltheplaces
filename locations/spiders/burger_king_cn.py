from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCNSpider(JSONBlobSpider):
    name = "burger_king_cn"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.bkchina.cn/website/new/js/area.js"]
    locations_key = ["data", "data"]

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_regions)

    def parse_regions(self, response):
        provinces_list = []
        provinces = {}
        for line in [line for line in response.text.split("\n") if "dsy.add(" in line]:
            code = line.split('add("')[1].split('",')[0]
            areas = parse_js_object(line)
            if "_" not in code and provinces == {}:
                provinces_list = areas
                provinces = {province: [] for province in areas}
            elif len(code.split("_")) == 2:
                provinces[provinces_list[int(code.split("_")[1])]] = areas
        for province, cities in provinces.items():
            for city in cities:
                yield from self.request_page(province, city, 1)

    def request_page(self, province, city, page):
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

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["state"] = response.meta["province"]
        apply_yes_no(Extras.BREAKFAST, item, location["hasBreakfast"] == "1", False)
        yield item
