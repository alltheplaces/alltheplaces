from scrapy import Spider
from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.items import Feature


class CarharttWipSpider(Spider):
    name = "carhartt_wip"
    item_attributes = {"brand": "Carhartt Work in Progress", "brand_wikidata": "Q123015694"}
    graphql_url = "https://carharrt-storefinder-api.herokuapp.com/graphql"

    def start_requests(self):
        for offset in range(0, 150, 50):
            yield JsonRequest(
                url=self.graphql_url,
                method="POST",
                data={
                    "operationName": "offline",
                    "variables": {
                        "withStores": True,
                        "withStockists": False,
                        "country": "",
                        "hasPosition": False,
                        "offset": offset,
                    },
                    "query": "fragment hours on Weekday {\n  openIntervals {\n    start\n    end\n    __typename\n  }\n  isClosed\n  __typename\n}\n\nfragment store on Store {\n  name\n  address {\n    line1\n    line2\n    city\n    postalCode\n    countryCode\n    __typename\n  }\n  displayCoordinate {\n    latitude\n    longitude\n    __typename\n  }\n mainPhone\n  emails\n c_storeType\n  c_tempClosed\n  hours {\n    monday {\n      ...hours\n      __typename\n    }\n    tuesday {\n      ...hours\n      __typename\n    }\n    wednesday {\n      ...hours\n      __typename\n    }\n    thursday {\n      ...hours\n      __typename\n    }\n    friday {\n      ...hours\n      __typename\n    }\n    saturday {\n      ...hours\n      __typename\n    }\n    sunday {\n      ...hours\n      __typename\n    }\n    __typename\n  }\n  websiteUrl {\n    url\n    __typename\n  }\n  meta {\n    uid\n    id\n    __typename\n  }\n  c_newsletter_URL\n  c_storedetailseiten_URL\n  __typename\n}\n\nfragment distance on Distance {\n  id\n  distanceKilometers\n  __typename\n}\n\nquery offline($withStores: Boolean!, $withStockists: Boolean!, $position: String, $hasPosition: Boolean!, $country: String!, $offset: Int!) {\n  stores(position: $position, country: $country, offset: $offset) @include(if: $withStores) {\n    entities {\n      ...store\n      __typename\n    }\n    distances @include(if: $hasPosition) {\n      ...distance\n      __typename\n    }\n    geo @include(if: $hasPosition) {\n      coordinate {\n        latitude\n        longitude\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  stockists(position: $position, country: $country, offset: $offset) @include(if: $withStockists) {\n    entities {\n      ...store\n      __typename\n    }\n    distances @include(if: $hasPosition) {\n      ...distance\n      __typename\n    }\n    geo @include(if: $hasPosition) {\n      coordinate {\n        latitude\n        longitude\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
                },
            )

    def parse(self, response):
        data = response.json()
        store_data = data.get("data").get("stores").get("entities")

        for store in store_data:
            oh = OpeningHours()
            day_data = store.get("hours") or {}
            day_dict = dict(day_data)
            for day, value in day_dict.items():
                if isinstance(value, str) or value.get("isClosed"):
                    continue
                for interval in value.get("openIntervals"):
                    oh.add_range(
                        day=day.title()[:2],
                        open_time=interval.get("start"),
                        close_time=interval.get("end"),
                        time_format="%H:%M",
                    )
            emails = store.get("emails")
            properties = {
                "ref": store.get("meta").get("uid"),
                "name": store.get("name"),
                "street_address": store.get("address").get("line1"),
                "city": store.get("address").get("city"),
                "phone": store.get("mainPhone"),
                "email": emails[0] if emails else None,
                "postcode": store.get("address").get("postalCode"),
                "country": store.get("address").get("countryCode"),
                "lat": store.get("displayCoordinate").get("latitude"),
                "lon": store.get("displayCoordinate").get("longitude"),
                "website": f"https://www.carhartt-wip.com{store.get('c_storedetailseiten_URL')}",
                "opening_hours": oh.as_opening_hours(),
            }
            yield Feature(**properties)
