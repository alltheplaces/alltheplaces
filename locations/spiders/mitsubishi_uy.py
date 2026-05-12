from scrapy import Spider
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class MitsubishiUYSpider(Spider):
    name = "mitsubishi_uy"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://www.mitsubishi-motors.com.uy/concesionarios"]

    def parse(self, response):
        for shop_node in response.css("a.link-ubicacion"):
            item = Feature()
            name = shop_node.xpath('.//*[@fs-list-field="nombre"]/text()').get("").strip()
            item["street_address"] = shop_node.xpath('.//*[@fs-list-field="direccion"]/text()').get()
            item["phone"] = shop_node.xpath('.//*[@fs-list-field="telefono"]/text()').get()
            item["email"] = shop_node.xpath('.//*[@fs-list-field="mail"]/text()').get()

            dept = shop_node.xpath('.//*[@fs-list-field="departamento"]/text()').get(default="").strip()
            # Combine name and department for a unique ref and descriptive branch
            item["ref"] = item["branch"] = f"{name} - {dept}" if dept else name

            if map_url := shop_node.xpath("./@data-map").get():
                extract_google_position(item, Selector(text=f'<a href="{map_url}"></a>'))

            apply_category(Categories.SHOP_CAR, item)
            yield item
