from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature


class MitsubishiUYSpider(Spider):
    name = "mitsubishi_uy"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.com.uy/concesionarios"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for shop_node in response.css("a.link-ubicacion"):
            item = Feature()
            item["ref"] = item["name"] = shop_node.xpath('.//*[@fs-list-field="nombre"]/text()').get("").strip()
            item["street_address"] = shop_node.xpath('.//*[@fs-list-field="direccion"]/text()').get()
            item["phone"] = shop_node.xpath('.//*[@fs-list-field="telefono"]/text()').get()
            item["email"] = shop_node.xpath('.//*[@fs-list-field="mail"]/text()').get()

            if map_url := shop_node.xpath("./@data-map").get():
                item["lat"], item["lon"] = url_to_coords(map_url)

            apply_category(Categories.SHOP_CAR, item)
            yield item
