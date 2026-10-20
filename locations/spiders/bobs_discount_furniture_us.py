from typing import Iterable

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BobsDiscountFurnitureUSSpider(XMLFeedSpider):
    name = "bobs_discount_furniture_us"
    item_attributes = {"brand": "Bob's Discount Furniture", "brand_wikidata": "Q4931582"}
    allowed_domains = ["www.mybobs.com"]
    start_urls = ["https://api.mybobs.com/occ/v2/bobsspa/stores?pageSize=1000&fields=FULL"]
    iterator = "iternodes"
    itertag = "stores"

    def parse_node(self, response: Response, node: Selector) -> Iterable[Feature]:
        if node.xpath(".//isComingSoon/text()").get() == "true":
            return
        if node.xpath(".//isStoreOpen/text()").get() == "false":
            return

        properties = {
            "ref": node.xpath(".//eccStoreId/text()").get(),
            "branch": node.xpath(".//displayName/text()").get(),
            "street_address": node.xpath(".//address/line1/text()").get(),
            "city": node.xpath(".//address/town/text()").get(),
            "state": node.xpath(".//address/region/isocodeShort/text()").get(),
            "postcode": node.xpath(".//address/postalCode/text()").get(),
            "country": node.xpath(".//address/country/isocode/text()").get(),
            "phone": node.xpath(".//address/phone/text()").get(),
            "lat": node.xpath(".//geoPoint/latitude/text()").get(),
            "lon": node.xpath(".//geoPoint/longitude/text()").get(),
        }

        url_path = node.xpath("./url/text()").get("")
        if url_path:
            properties["website"] = "https://www.mybobs.com" + url_path.strip().split("?")[0]

        properties["opening_hours"] = self.parse_opening_hours(node)

        apply_category(Categories.SHOP_FURNITURE, properties)

        yield Feature(**properties)

    def parse_opening_hours(self, node: Selector) -> OpeningHours:
        opening_hours = OpeningHours()
        for day_entry in node.xpath(".//openingHours/weekDayOpeningList"):
            if day_entry.xpath(".//closed/text()").get() == "true":
                continue
            day = day_entry.xpath(".//weekDay/text()").get()
            open_time = day_entry.xpath(".//openingTime/formattedHour/text()").get()
            close_time = day_entry.xpath(".//closingTime/formattedHour/text()").get()
            if day and open_time and close_time:
                opening_hours.add_range(
                    day=day.strip()[:2],
                    open_time=open_time.strip(),
                    close_time=close_time.strip(),
                    time_format="%I:%M %p",
                )
        return opening_hours
