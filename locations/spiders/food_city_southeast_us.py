from scrapy import Request, Spider

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class FoodCitySoutheastUSSpider(Spider):
    name = "food_city_southeast_us"
    item_attributes = {
        "brand": "Food City",
        "brand_wikidata": "Q16981107",
    }

    def _make_request(self, offset):
        return Request(
            f"https://www.foodcity.com/index.php?vica=ctl_storelocations&vicb=showNextStoresForStoreSelector&pageCount={offset}"
        )

    def start_requests(self):
        yield self._make_request(0)

    def parse(self, response):
        listings = response.css("div.store-listing")

        for store_listing in listings:
            item = Feature()
            item["lat"] = store_listing.xpath("@data-lat").get()
            item["lon"] = store_listing.xpath("@data-lng").get()
            item["ref"] = store_listing.xpath("@data-id").get()
            item["website"] = f"https://www.foodcity.com/stores/store-details/{item['ref']}"
            item["street_address"] = store_listing.xpath(".//span[@class='street-address']/text()").get()
            item["city"] = store_listing.xpath(".//span[@class='city']/text()").get()
            item["state"] = store_listing.xpath(".//abbr[@class='state']/text()").get()
            item["postcode"] = store_listing.xpath(".//span[@class='postal-code']/text()").get()
            item["phone"] = store_listing.xpath(".//div[@class='tel']/a/@href").get().removeprefix("tel:")
            item["opening_hours"] = self.parse_opening_hours(
                store_listing.xpath(".//label[text()='Store Hours']/../text()").getall()
            )
            item["extras"]["opening_hours:pharmacy"] = self.parse_opening_hours(
                store_listing.xpath(".//label[text()='Pharmacy Hours']/../text()").getall()
            ).as_opening_hours()
            apply_yes_no(Extras.DELIVERY, item, bool(store_listing.xpath(".//img[@src='/images/home-delivery.png']")))
            yield item

        if len(listings) == 10:
            currentOffset = int(response.xpath("//input[@id='pageCount']/@value").get())
            yield self._make_request(currentOffset + len(listings))

    def parse_opening_hours(self, lines):
        oh = OpeningHours()
        for line in lines:
            i = line.rfind(" ")
            oh.add_ranges_from_string(line[i + 1 :] + " " + line[:i])
        return oh
