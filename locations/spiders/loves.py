from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class LovesSpider(scrapy.Spider):
    name = "loves"
    SPEEDCO = {"brand": "Speedco", "brand_wikidata": "Q112455073"}
    item_attributes = {"brand": "Love's", "brand_wikidata": "Q1872496"}
    allowed_domains = ["www.loves.com"]
    page = 0

    def start_requests(self):
        yield JsonRequest(
            f"https://www.loves.com/api/sitecore/StoreSearch/SearchStoresWithDetail?pageNumber={self.page}&top=50&lat=0&lng=0"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()
        if not stores:
            return
        for store in stores:
            item = Feature(
                branch=store["PreferredName"],
                ref=store["SiteId"],
                street_address=store["Address"],
                city=store["City"],
                state=store["State"],
                postcode=store["Zip"],
                phone=store["MainPhone"],
                email=store["MainEmail"],
                lat=float(store["Latitude"]),
                lon=float(store["Longitude"]),
            )

            item["website"] = "https://www.loves.com/locations/{}".format(store["SiteName"].split(" ")[-1])

            if store["IsLoveStore"] is True:
                apply_category({"highway": "services"}, item)
            elif store["IsSpeedCo"] is True:
                item.update(self.SPEEDCO)
                apply_category(Categories.SHOP_TRUCK_REPAIR, item)
            elif store["IsHotel"] is True:
                apply_category(Categories.HOTEL, item)
                continue  # ChoiceHotelsSpider

            yield item

        self.page += 1
        next_page = f"https://www.loves.com/api/sitecore/StoreSearch/SearchStoresWithDetail?pageNumber={self.page}&top=50&lat=0&lng=0"
        yield response.follow(next_page, callback=self.parse)
