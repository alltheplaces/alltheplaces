from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_CZ
from locations.items import Feature


class HruskaCZSpider(Spider):
    name = "hruska_cz"
    item_attributes = {"brand": "Hruška", "brand_wikidata": "Q58196374"}
    allowed_domains = ["mojehruska.cz"]
    start_urls = ["https://mojehruska.cz/prodejny/"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.xpath('//div[@class="prodejny"]/div[position()>1]'):
            properties = {
                "street_address": store.xpath('./div[3]/text()').get(),
                "city": store.xpath('./div[4]/text()').get(),
                "postcode": store.xpath('./div[5]/text()').get(),
                "phone": store.xpath('./div[6]/text()').get(),
                "opening_hours": OpeningHours(),
            }
            if store_name := store.xpath('./div[2]/text()').get():
                if store_name.startswith("Hruška č. "):
                    properties["ref"] = store_name.split("Hruška č. ", 1)[1]
                else:
                    properties["name"] = store_name
            hours_text = " ".join(store.xpath('./div[position()>6]').getall())
            properties["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_CZ)
            apply_category(Categories.SHOP_CONVENIENCE, properties)
            yield Feature(**properties)
