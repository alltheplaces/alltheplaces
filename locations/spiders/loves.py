import json

import scrapy
from scrapy.exceptions import CloseSpider

from locations.categories import Categories, apply_category
from locations.items import Feature

HEADERS = {"Content-Type": "application/json"}


class LovesSpider(scrapy.Spider):
    name = "loves"
    item_attributes = {"brand": "Love's", "brand_wikidata": "Q1872496"}
    allowed_domains = ["www.loves.com"]
    download_delay = 0.2
    page = 0

    def start_requests(self):
        payload = json.dumps(
            {
                "StoreTypes": [],
                "Amenities": [],
                "Restaurants": [],
                "FoodConcepts": [],
                "State": "All",
                "City": "All",
                "Highway": "All",
            }
        )
        yield scrapy.Request(
            f"https://www.loves.com/api/sitecore/StoreSearch/SearchStoresWithDetail?pageNumber={0}&top=50&lat=39.09574818760951&lng=-96.9935195",
            method="POST",
            body=payload,
            headers=HEADERS,
        )

    def parse(self, response):
        stores = response.json()
        if not stores:
            raise CloseSpider()
        for store in stores:
            item = Feature(
                name=store["SiteName"],
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

            if store["IsLoveStore"] is True:
                apply_category({"highway": "service"}, item)
            elif store["IsCountryStore"] is True:
                apply_category(Categories.FUEL_STATION, item)
            elif store["IsSpeedCo"] is True:
                apply_category({"shop": "truck_repair"}, item)

            yield item

        self.page += 1
        next_page = f"https://www.loves.com/api/sitecore/StoreSearch/SearchStoresWithDetail?pageNumber={self.page}&top=50&lat=39.09574818760951&lng=-96.9935195"
        yield response.follow(next_page, callback=self.parse)
