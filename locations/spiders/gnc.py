import scrapy
from locations.items import GeojsonPointItem

import json
import re
import time
import random

STATE_CENTROID_ZIPS = [
    "26601",
    "34604",
    "61749",
    "56425",
    "20716",
    "02818",
    "83227",
    "03226",
    "27330",
    "05669",
    "06023",
    "19946",
    "87036",
    "93645",
    "08515",
    "54443",
    "97754",
    "68856",
    "16835",
    "98847",
    "71369",
    "31044",
    "36750",
    "84642",
    "43317",
    "76873",
    "80827",
    "29061",
    "73114",
    "37132",
    "82638",
    "96706",
    "58463",
    "40033",
    "96910",
    "04426",
    "13310",
    "89310",
    "99756",
    "49621",
    "72113",
    "39094",
    "65064",
    "59464",
    "67427",
    "46278",
    "00720",
    "57501",
    "01757",
    "23921",
    "50201",
    "85544",
]

BASE_URL = (
    "https://www.gnc.com/on/demandware.store/Sites-GNC-Site/default/Stores-FindStores"
)


class GNCSpider(scrapy.Spider):
    name = "gnc"
    item_attributes = {"brand": "GNC"}
    allowed_domains = ["www.gnc.com"]
    download_delay = 30
    start_urls = ("https://www.gnc.com/stores",)
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
        "CONCURRENT_REQUESTS": "1",
    }

    def parse(self, response):
        url = BASE_URL
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        for zipcode in STATE_CENTROID_ZIPS:
            form_data = {
                "dwfrm_storelocator_countryCode": "US",
                "dwfrm_storelocator_distanceUnit": "mi",
                "dwfrm_storelocator_maxdistance": "500",
                "dwfrm_storelocator_findbyzip": "Search",
                "dwfrm_storelocator_postalCode": zipcode,
            }

            time.sleep(random.randint(1, 10))
            yield scrapy.http.FormRequest(
                url=url,
                method="POST",
                formdata=form_data,
                headers=headers,
                callback=self.parse_store_list,
            )

    def parse_store_list(self, response):
        content = response.xpath(
            '//script[contains(text(), "map.data.addGeoJson")]/text()'
        ).extract_first()
        data = json.loads(
            re.search(r"JSON.parse\( eqfeed_callback\((.*?)\) \) \);", content).group(1)
        )
        stores = data["features"]

        for store in stores:
            properties = {
                "ref": store["properties"]["storenumber"],
                "name": store["properties"]["title"],
                "addr_full": store["properties"]["address1"],
                "city": store["properties"]["city"],
                "state": store["properties"]["state"],
                "postcode": store["properties"]["postalCode"],
                "lat": store["geometry"]["coordinates"][1],
                "lon": store["geometry"]["coordinates"][0],
                "website": "".join(
                    [
                        "www.gnc.com",
                        re.search(r'href="(.*?)"', store["properties"]["url"]).group(1),
                    ]
                ),
            }

            yield GeojsonPointItem(**properties)
