from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class ColonialParkingUSSpider(Spider):
    name = "colonial_parking_us"
    item_attributes = {"brand": "Colonial Parking", "brand_wikidata": "Q121494114"}
    start_urls = [
        "https://www.ecolonial.com/wp-admin/admin-ajax.php?action=mapmarkers&ne_lat=90&ne_lng=180&sw_lat=-90&sw_lng=-180"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            apply_category(Categories.PARKING, item)
            yield Request(
                url=f'https://www.ecolonial.com/wp-admin/admin-ajax.php?action=facility&id={item["ref"]}',
                callback=self.parse_location_details,
                cb_kwargs={"item": item},
            )

    def parse_location_details(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["addr_full"] = response.xpath('//*[@class="adresse"]/span/text()').get()
        item["phone"] = response.xpath('//*[contains(text(), "Phone")]/following-sibling::span/text()').get()
        yield item
