from typing import Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaUASpider(Spider):
    name = "mazda_ua"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["mazda.ua"]
    start_urls = ["https://mazda.ua/find-a-dealer/?name=*"]

    def parse(self, response: Response) -> Iterable[Feature]:
        js_blob = response.xpath('//script[contains(text(), "var markers1 = [")]/text()').get()
        js_blob = "[" + js_blob.split("var markers1 = [", 1)[1].split("];", 1)[0] + "]"
        markers = parse_js_object(js_blob)
        for marker in markers:
            properties = {
                "name": marker["title"],
                "lat": marker["lat"],
                "lon": marker["lng"],
            }
            if marker.get("site"):
                properties["website"] = marker["site"]
            if marker.get("sellAddress"):
                sales_item = Feature(**properties)
                sales_item["ref"] = str(marker["id"]) + "_Sales"
                sales_item["addr_full"] = marker["sellAddress"]
                if marker.get("sellPhone"):
                    sales_item["phone"] = marker["sellPhone"]
                if marker.get("sellEmail"):
                    sales_item["email"] = marker["sellEmail"]
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item
            if marker.get("serviceAddress"):
                service_item = Feature(**properties)
                service_item["ref"] = str(marker["id"]) + "_Service"
                service_item["addr_full"] = marker["serviceAddress"]
                if marker.get("servicePhone"):
                    service_item["phone"] = marker["servicePhone"]
                if marker.get("serviceEmail"):
                    service_item["email"] = marker["serviceEmail"]
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
