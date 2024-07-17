from scrapy import Spider

from locations.categories import Categories
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class NinetynineBikesAUSpider(Spider):
    name = "99_bikes_au"
    item_attributes = {"brand": "99 Bikes", "brand_wikidata": "Q110288298", "extras": Categories.SHOP_BICYCLE.value}
    allowed_domains = ["www.99bikes.com.au"]
    start_urls = ["https://www.99bikes.com.au//rest/V1/clickandcollect_getalllocations"]

    def parse(self, response):
        for item in response.xpath("item"):
            store = {}
            store["ref"] = item.xpath("id/text()").get()
            store["name"] = item.xpath("store_name/text()").get()
            store["email"] = item.xpath("email/text()").get()
            # store["fax"] = item.xpath("fax/text()").get()

            store["lat"] = item.xpath("latitude/text()").get()
            store["lon"] = item.xpath("longitude/text()").get()

            store["city"] = item.xpath("city/text()").get()
            store["phone"] = item.xpath("phone/text()").get()

            store["state"] = item.xpath("state/text()").get()
            store["postcode"] = item.xpath("postcode/text()").get()
            store["street_address"] = item.xpath("address/text()").get()

            store["opening_hours"] = OpeningHours()
            for opening_time in item.xpath("extension_attributes/opening_time/item"):
                day = opening_time.xpath("day/text()").get()
                open_time = opening_time.xpath("open_time/text()").get()
                close_time = opening_time.xpath("close_time/text()").get()

                store["opening_hours"].add_range(DAYS_EN[day], open_time, close_time, "%H:%M%p")
            yield Feature(**store)
