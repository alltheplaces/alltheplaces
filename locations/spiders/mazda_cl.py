from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, OpeningHours
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaCLSpider(scrapy.Spider):
    name = "mazda_cl"
    item_attributes = MAZDA_SHARED_ATTRIBUTES

    start_urls = ["https://www.mazda.cl/concesionarios/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for dealer in response.xpath('//*[@class="dealers-block-list"]//*[@class="dealer-card"]'):
            item = Feature()
            item["name"] = item["ref"] = dealer.xpath('.//*[@class="dealer-info-name"]/text()').get()
            item["street_address"] = dealer.xpath('.//*[@class="dealer-info-address"]/text()').get()
            item["phone"] = dealer.xpath('.//*[@class="dealer-info-phone-number"]/text()').get()

            for section in dealer.xpath('.//*[@class="dealer-shift-sets"]/div'):
                service_name = (
                    section.xpath('.//*[@class="dealer-info-shift-set-title"]/text()').get(default="").strip()
                )

                oh = OpeningHours()

                for hours_text in section.xpath('.//*[@class="dealer-shift"]').xpath("normalize-space()").getall():
                    oh.add_ranges_from_string(
                        hours_text.replace(" a ", "-"),
                        DAYS_ES,
                    )

                if service_name == "Venta":
                    item = item.deepcopy()
                    apply_category(Categories.SHOP_CAR, item)
                    item["opening_hours"] = oh
                    yield item

                elif service_name == "Servicios":
                    item = item.deepcopy()
                    item["ref"] = f"{item['ref']}-SERVICE"
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                    item["opening_hours"] = oh
                    yield item
