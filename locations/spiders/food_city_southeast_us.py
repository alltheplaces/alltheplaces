from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class FoodCitySoutheastUSSpider(Spider):
    name = "food_city_southeast_us"
    item_attributes = {
        "brand": "Food City",
        "brand_wikidata": "Q16981107",
    }
    page_size = 10

    def _make_request(self, offset) -> Request:
        return Request(
            f"https://www.foodcity.com/index.php?vica=ctl_storelocations&vicb=showNextStoresForStoreSelector&pageCount={offset}",
            meta=dict(offset=offset),
        )

    def start_requests(self) -> Iterable[Request]:
        yield self._make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        listings = response.xpath('//*[contains(@id,"store-listing")]')

        for store_listing in listings:
            lat = store_listing.xpath("@data-lat").get()
            lon = store_listing.xpath("@data-lng").get()
            if lat == "0":
                continue  # skip duplicate store data without coordinates
            item = Feature()
            ref = store_listing.xpath("@data-id").get()
            item["lat"], item["lon"] = lat, lon
            item["ref"] = ref
            item["website"] = f"https://www.foodcity.com/stores/store-details/{ref}"
            # These hidden input tags are siblings to store_listing
            item["street_address"] = store_listing.xpath(f"..//input[@id='Address{ref}']/@value").get()
            item["city"] = store_listing.xpath(f"..//input[@id='City{ref}']/@value").get()
            item["state"] = store_listing.xpath(f"..//input[@id='State{ref}']/@value").get()
            item["postcode"] = store_listing.xpath(f"..//input[@id='Zip{ref}']/@value").get()

            item["phone"] = (
                store_listing.xpath(".//div[@class='location']//a[@class='tel']/@href").get().removeprefix("tel:")
            )
            for location_hours in store_listing.xpath(".//*[@class='hours']"):
                h2 = location_hours.xpath("./h2/text()").get()
                if h2 == "Store Hours":
                    item["opening_hours"] = self.parse_opening_hours(
                        location_hours.xpath("./p/text()").getall()
                    ).as_opening_hours()
                if h2 == "Pharmacy Hours":
                    item["extras"]["opening_hours:pharmacy"] = self.parse_opening_hours(
                        location_hours.xpath("./p/text()").getall()
                    ).as_opening_hours()
            apply_yes_no(
                Extras.DELIVERY, item, bool(store_listing.xpath(".//img[contains(@src, '/home-delivery.png')]"))
            )
            yield item

        if len(listings) == self.page_size:
            yield self._make_request(response.meta["offset"] + self.page_size)

    def parse_opening_hours(self, lines: list) -> OpeningHours:
        oh = OpeningHours()
        for line in lines:
            i = line.rfind(" ")
            oh.add_ranges_from_string(line[i + 1 :] + " " + line[:i])
        return oh
