from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class MitsubishiPESpider(scrapy.Spider):
    name = "mitsubishi_pe"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.com.pe/concesionarios"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for value in response.xpath('//*[@id="dep"]//option//@value').getall():
            yield scrapy.Request(
                url="https://www.mitsubishi-motors.com.pe/concesionarios?tipo=todos&dep={}".format(value),
                callback=self.parse_details,
            )

    def parse_details(self, response, **kwargs):
        for location in response.xpath('//*[@class="block-concesionario"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h3[2]/text()").get()
            item["addr_full"] = location.xpath(".//p/text()").get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            extract_google_position(item, location)
            location_type = location.xpath(".//ul//li").xpath("normalize-space()").getall()

            for dept in location_type:
                if dept == "Concesionario":
                    sales_item = item.deepcopy()
                    sales_item["ref"] = sales_item["branch"] + "-SALES"
                    apply_category(Categories.SHOP_CAR, sales_item)
                    yield sales_item
                elif dept == "Taller":
                    service_item = item.deepcopy()
                    service_item["ref"] = service_item["branch"] + "-SERVICE"
                    apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                    yield service_item
                elif dept == "Repuestos":
                    spare_parts_item = item.deepcopy()
                    spare_parts_item["ref"] = spare_parts_item["branch"] + "-SPARE_PARTS"
                    apply_category(Categories.SHOP_CAR_PARTS, spare_parts_item)
                    yield spare_parts_item
