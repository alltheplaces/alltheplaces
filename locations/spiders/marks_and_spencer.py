# -*- coding: utf-8 -*-
import json
import scrapy
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class MarksAndSpencerSpider(scrapy.Spider):
    name = "marks_and_spencer"
    item_attributes = {"brand": "Marks and Spencer"}
    start_urls = (
        "https://www.marksandspencer.com/webapp/wcs/stores/servlet/MSResStoreFinderConfigCmd?storeId=10151&langId=-24",
    )

    def parse(self, response):
        config = json.loads(
            response.text.replace("STORE_FINDER_CONFIG=", "")
        )
        stores_api_url = (
            f"{config['storeFinderAPIBaseURL']}?apikey={config['apiConsumerKey']}"
        )
        yield response.follow(stores_api_url, self.parse_stores)

    def parse_stores(self, response):
        stores = response.json()
        for store in stores["results"]:
            properties = {
                "ref": store["id"],
                "name": store["name"],
                "addr_full": f"{store['address']['addressLine1']}, {store['address']['addressLine2']}",
                "city": store["address"]["city"],
                "country": store["address"]["country"],
                "postcode": store["address"]["postalCode"],
                "lat": store["coordinates"]["latitude"],
                "lon": store["coordinates"]["longitude"],
                "phone": store.get("phone", ""),
                "opening_hours": self.get_opening_hours(store),
            }
            yield GeojsonPointItem(**properties)

    def get_opening_hours(self, store):
        o = OpeningHours()
        for day in store["coreOpeningHours"]:
            o.add_range(
                day["day"][:2], day["open"], day["close"].replace("24:00", "23:59")
            )
        return o.as_opening_hours()
