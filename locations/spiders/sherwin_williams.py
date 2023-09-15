import html
import json
from urllib.parse import urlencode

import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points
from locations.user_agents import BROWSER_DEFAULT


class SherwinWilliamsSpider(scrapy.Spider):
    name = "sherwin_williams"
    item_attributes = {"brand": "Sherwin-Williams", "brand_wikidata": "Q48881"}
    allowed_domains = ["www.sherwin-williams.com"]
    user_agent = BROWSER_DEFAULT

    #  Covers United States, Canada, UK, Puerto Rico, Bahamas with 500 mile radius - (from regis spider)
    lats = [
        "32.806671",
        "31.054487",
        "39.059811",
        "46.921925",
        "45.694454",
        "38.039119",
        "44.045876",
        "32.593106",
        "33.596319",
        "47.398349",
        "24.44715",
        "18.229351",
        "19.725342",
        "64.014496",
        "51.563412",
        "52.48278",
        "55.27911529201562",
        "55.17886766328199",
        "63.15435519659188",
        "52.96187505907603",
    ]

    lons = [
        "-86.791130",
        "-97.563461",
        "-105.311104",
        "-110.454353",
        "-93.900192",
        "-87.618638",
        "-72.710686",
        "-82.342529",
        "-113.334961",
        "-121.289062",
        "-78.00293",
        "-65.830078",
        "-155.610352",
        "-153.28125" "-86.923828",
        "-65.126953",
        "-103.974609375",
        "-120.76171875",
        "-136.142578125",
        "-0.17578125",
    ]

    def start_requests(self):
        params = {
            "sideBarType": "LSTORES",
            "radius": "50",
            "abbrv": "us",
            "uom": "SMI",
            "langId": "-1",
            "storeId": "10151",
        }
        base_url = "https://www.sherwin-williams.com/AjaxStoreLocatorSideBarView?"

        addtional_lat_lons = [
            (32.790133, -97.304605),
            (32.789066, -96.893189),
            (49.245301, -123.130791),
            (38.919445, -77.055250),
            (39.297416, -76.652098),
            (33.675832, -84.390719),
            (33.840679, -84.391333),
        ]

        # paint stores - search by 100 mile radius in US/CA
        with open_searchable_points("us_centroids_50mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                params.update({"latitude": lat, "longitude": lon, "storeType": "PaintStore"})
                yield scrapy.Request(
                    url=base_url + urlencode(params),
                    callback=self.parse,
                    meta={"store_type": "Sherwin-Williams Paint Store"},
                )

        with open_searchable_points("ca_centroids_50mile_radius.csv") as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                params.update({"latitude": lat, "longitude": lon, "storeType": "PaintStore"})
                yield scrapy.Request(
                    url=base_url + urlencode(params),
                    callback=self.parse,
                    meta={"store_type": "Sherwin-Williams Paint Store"},
                )

        for lat, lon in addtional_lat_lons:
            params.update({"latitude": lat, "longitude": lon, "storeType": "PaintStore"})
            yield scrapy.Request(
                url=base_url + urlencode(params),
                callback=self.parse,
                meta={"store_type": "Sherwin-Williams Paint Store"},
            )

        # the other store types are much more sparse so we can search with a larger
        # radius before hitting the limit of stores returned
        store_types = [
            ("FloorCoveringStore", "Sherwin-Williams Floorcovering Store"),
            ("CommercialPaintStore", "Sherwin-Williams Commercial Paint Store"),
            ("FinishesStore", "Sherwin-Williams Product Finishes Facility"),
            ("SprayEquipmentStore", "Sherwin-Williams Spray Equipment Store"),
        ]

        for store_type, type_name in store_types:
            for lat, lon in zip(self.lats, self.lons):
                params.update(
                    {
                        "storeType": store_type,
                        "radius": "500",
                        "latitude": lat,
                        "longitude": lon,
                    }
                )
                yield scrapy.Request(
                    url=base_url + urlencode(params),
                    callback=self.parse,
                    meta={"store_type": type_name},
                )

    def parse(self, response):
        json_data = response.xpath('//script[@id="storeResultsJSON"]/text()').extract_first()
        if json_data:
            data = json.loads(json_data)
            store_type = response.meta["store_type"]

            for store in data["stores"]:
                properties = {
                    "ref": store["storeNumber"],
                    "name": store["name"],
                    "addr_full": html.unescape(store["address"].strip()),
                    "city": store["city"].strip(),
                    "state": store["state"].strip(),
                    "postcode": store["zipcode"].strip(),
                    "phone": store["phone"].strip(),
                    "lat": float(store["latitude"]),
                    "lon": float(store["longitude"]),
                    "website": "https://www.sherwin-williams.com" + store["url"],
                    "brand": store_type,
                    "extras": {
                        "number": store["storeNumber"],
                    },
                }

                yield Feature(**properties)
