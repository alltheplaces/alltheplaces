from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class InnoutSpider(Spider):
    name = "innout"
    item_attributes = {"brand": "In-N-Out Burger", "brand_wikidata": "Q1205312"}
    allowed_domains = ["www.in-n-out.com"]
    start_urls = [
        "https://locations.in-n-out.com/api/finder/search/?showunopened=false&latitude=37.751&longitude=-97.822&maxdistance=3050&maxresults=2500"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        response.selector.remove_namespaces()

        for store_elem in response.xpath("//LocationFinderStore"):
            city = store_elem.xpath("./City/text()").extract_first()
            lat = store_elem.xpath("./Latitude/text()").extract_first()
            lon = store_elem.xpath("./Longitude/text()").extract_first()
            ref = store_elem.xpath("./StoreNumber/text()").extract_first()
            addr_full = store_elem.xpath("./StreetAddress/text()").extract_first()
            zipcode = store_elem.xpath("./ZipCode/text()").extract_first()
            state = store_elem.xpath("./State/text()").extract_first()
            name = store_elem.xpath("./Name/text()").extract_first()

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

            apply_yes_no(Extras.INDOOR_SEATING, item, store_elem.xpath("./HasDiningRoom/text()").get() == "true")
            apply_yes_no(Extras.DRIVE_THROUGH, item, store_elem.xpath("./HasDriveThru/text()").get() == "true")

            apply_category(Categories.FAST_FOOD, item)

            yield item
