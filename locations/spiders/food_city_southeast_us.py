from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FoodCitySoutheastUSSpider(Spider):
    name = "food_city_southeast_us"
    item_attributes = {
        "brand": "Food City",
        "brand_wikidata": "Q16981107",
    }
    page_size = 10

    def _make_request(self, offset):
        return Request(
            f"https://www.foodcity.com/index.php?vica=ctl_storelocations&vicb=showNextStoresForStoreSelector&pageCount={offset}",
            meta=dict(offset=offset),
        )

    def start_requests(self):
        yield self._make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        listings = response.xpath('//*[contains(@id,"store-listing")]')

        for store_listing in listings:
            item = Feature()
            item["lat"] = store_listing.xpath("@data-lat").get()
            item["lon"] = store_listing.xpath("@data-lng").get()
            item["ref"] = store_listing.xpath("@data-id").get()
            item["website"] = f"https://www.foodcity.com/stores/store-details/{item['ref']}"
            item["addr_full"] = clean_address(store_listing.xpath(".//*[@class='location']/p/text()").getall()).split(
                "miles"
            )[-1]
            item["phone"] = store_listing.xpath(".//a[contains(@href,'tel')]/@href").get()
            item["opening_hours"] = self.parse_opening_hours(
                store_listing.xpath(".//label[text()='Store Hours']/../text()").getall()
            )
            item["extras"]["opening_hours:pharmacy"] = self.parse_opening_hours(
                store_listing.xpath(".//label[text()='Pharmacy Hours']/../text()").getall()
            ).as_opening_hours()
            apply_yes_no(Extras.DELIVERY, item, bool(store_listing.xpath(".//img[@src='/images/home-delivery.png']")))
            yield item

        if len(listings) == self.page_size:
            yield self._make_request(response.meta["offset"] + self.page_size)

    def parse_opening_hours(self, lines):
        oh = OpeningHours()
        for line in lines:
            i = line.rfind(" ")
            oh.add_ranges_from_string(line[i + 1 :] + " " + line[:i])
        return oh
