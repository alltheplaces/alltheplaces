from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class InnoutSpider(Spider):
    name = "innout"
    item_attributes = {"brand": "In-N-Out Burger", "brand_wikidata": "Q1205312"}
    allowed_domains = ["locations.in-n-out.com", "www.in-n-out.com"]
    start_urls = [
        "https://locations.in-n-out.com/api/finder/search/?showunopened=false&latitude=37.751&longitude=-97.822&maxdistance=3050&maxresults=2500"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        response.selector.remove_namespaces()

        for store_elem in response.xpath("//LocationFinderStore"):
            city = store_elem.xpath("./City/text()").get()
            lat = store_elem.xpath("./Latitude/text()").get()
            lon = store_elem.xpath("./Longitude/text()").get()
            ref = store_elem.xpath("./StoreNumber/text()").get()
            addr_full = store_elem.xpath("./StreetAddress/text()").get()
            zipcode = store_elem.xpath("./ZipCode/text()").get()
            state = store_elem.xpath("./State/text()").get()
            name = store_elem.xpath("./Name/text()").get()

            properties = {
                "branch": name,
                "street_address": addr_full,
                "city": city,
                "state": state,
                "postcode": zipcode,
                "ref": ref,
                "website": "http://locations.in-n-out.com/" + ref,
                "lon": float(lon),
                "lat": float(lat),
                "image": store_elem.xpath("./ImageUrlLarge/text()").get(),
                "extras": {"start_date": store_elem.xpath("./OpenDate/text()").get().split("T", 1)[0]},
            }
            item = Feature(**properties)

            apply_yes_no(
                Extras.INDOOR_SEATING,
                item,
                store_elem.xpath("./HasDiningRoom/text()").get() == "true",
            )
            apply_yes_no(
                Extras.DRIVE_THROUGH,
                item,
                store_elem.xpath("./HasDriveThru/text()").get() == "true",
            )

            apply_category(Categories.FAST_FOOD, item)

            yield item
