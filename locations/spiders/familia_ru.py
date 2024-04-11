import json

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class FamiliaRUSpider(scrapy.Spider):
    name = "familia_ru"
    allowed_domains = ["www.famil.ru"]
    # TODO: create Wikidata page for this brand
    item_attributes = {"brand": "Familia"}
    start_urls = ["https://www.famil.ru/shops/"]

    def parse(self, response):
        coords_and_ids = response.xpath("//script[contains(text(), 'window.object_list')]/text()").re_first(
            r"window\.object_list = (.*?);"
        )
        coords_and_ids = json.loads(coords_and_ids)
        for coord_and_id in coords_and_ids:
            shop_info = response.xpath(f"//div[@data-id='{coord_and_id['id']}']")
            item = Feature()
            item["ref"] = coord_and_id["id"]
            item["lat"] = coord_and_id["lat"]
            item["lon"] = coord_and_id["long"]
            item["name"] = shop_info.xpath(".//div[@class='main__shops-sect-info__item-title']/text()").get()

            other_info = shop_info.xpath('.//div[@class="main__shops-sect-info__item-text"]/text()').getall()

            item["street_address"] = other_info[0].replace("Адрес: ", "")
            item["phone"] = other_info[1].replace("Телефон: ", "")

            hours = other_info[2].replace("Часы работы: ", "")
            hours = hours.replace("с ", "").split(" до ")
            oh = OpeningHours()
            oh.add_days_range(DAYS, hours[0].strip(), hours[1].strip())
            item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
