from copy import deepcopy
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature


class MitsubishiPESpider(scrapy.Spider):
    name = "mitsubishi_pe"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.com.pe/concesionarios"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for value in response.xpath('//*[@id="dep"]//option//@value').getall():
            yield scrapy.Request(
                url="https://www.mitsubishi-motors.com.pe/concesionarios?tipo=todos&dep={}".format(value),
                callback=self.parse_details,
            )

    def apply_sales_category(self, item):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-sales"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def apply_service_category(self, item):
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-service"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def parse_details(self, response, **kwargs):
        for location in response.xpath('//*[@class="block-concesionario"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h3[2]/text()").get()
            item["addr_full"] = location.xpath(".//p/text()").get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            extract_google_position(item, location)
            location_type = location.xpath(".//ul//li").xpath("normalize-space()").getall()

            sales_available = "Concesionario" in location_type
            service_available = "Taller" in location_type
            parts_available = "Repuestos" in location_type

            if sales_available:
                sales_item = self.apply_sales_category(item)
                apply_yes_no(Extras.CAR_REPAIR, sales_item, service_available)
                apply_yes_no(Extras.CAR_PARTS, sales_item, parts_available)
                yield sales_item

            if service_available:
                service_item = self.apply_service_category(item)
                apply_yes_no(Extras.CAR_PARTS, service_item, parts_available)
                yield service_item

            if not sales_available and not service_available:
                # Parts-only location
                if parts_available:
                    apply_category(Categories.SHOP_CAR_PARTS, item)
                    yield item
                else:
                    self.logger.error(f"Unknown location type: {location_type}, {item['branch']}")
