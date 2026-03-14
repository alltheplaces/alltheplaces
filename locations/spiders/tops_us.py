from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class TopsUSSpider(Spider):
    name = "tops_us"
    item_attributes = {"brand": "Tops", "brand_wikidata": "Q7825137"}
    allowed_domains = ["www.topsmarkets.com"]
    start_urls = ["http://www.topsmarkets.com/StoreLocator/Store_MapLocation_S.las?State=all"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for feature in response.json():
            yield Request(
                url="https://www.topsmarkets.com/StoreLocator/Store?L={}&S=".format(feature["StoreNbr"]),
                meta={"item": Feature(ref=feature["StoreNbr"], lat=feature["Latitude"], lon=feature["Longitude"])},
                callback=self.parse_store_details,
            )

    def parse_store_details(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["branch"] = response.xpath("//h3/text()").get()
        item["addr_full"] = merge_address_lines(response.xpath('//p[@class="Address"]/text()').getall())
        item["phone"] = response.xpath('//p[@class="PhoneNumber"]/a/text()').get()
        item["website"] = response.url
        hours_text = response.xpath('//table[@id="hours_info-BS"]//dd/text()').get()
        if hours_text:
            hours_text = hours_text.upper().replace("24 HOURS", "00:01AM-11:59PM")
            if "MON" not in hours_text and "SAT" not in hours_text and "SUN" not in hours_text:
                hours_text = "MONDAY-SUNDAY: " + hours_text
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
