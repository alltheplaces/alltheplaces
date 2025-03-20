from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no, Extras

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

    def parse_details(self, response, **kwargs):
        for location in response.xpath('//*[@class="block-concesionario"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h3[2]/text()").get()
            item["addr_full"] = location.xpath(".//p/text()").get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            extract_google_position(item, location)
            location_type = location.xpath(".//ul//li").xpath("normalize-space()").getall()
            if "Concesionario" not in location_type:
                if "Taller" in location_type:
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                    apply_yes_no(Extras.CAR_PARTS, item, "Repuestos" in location_type)
                else:
                    apply_category(Categories.SHOP_CAR_PARTS, item)
            else:
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no(Extras.CAR_REPAIR, item, "Taller" in location_type)
                apply_yes_no(Extras.CAR_PARTS, item, "Repuestos" in location_type)
            yield item
