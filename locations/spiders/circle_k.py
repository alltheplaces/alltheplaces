# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

WIKIBRANDS = {
    "Circle K": "Q3268010",
    "Corner Store": "Q16959310",
    "Couche-Tard": "Q2836957",
    "Flash Foods": "Q16959310",
    "Kangaroo Express": "Q61747408",
    "Mac's": "Q4043527",
    "On The Run": "Q16931259",
}


class CircleKSpider(scrapy.Spider):

    name = "circle_k"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    allowed_domains = ["www.circlek.com"]

    start_urls = (
        "https://www.circlek.com/stores_new.php?lat=30.352998399999997&lng=-97.79609599999999&distance=80000&services=&region=global",
    )

    def parse(self, response):
        results = response.json()

        for storeid, store in results["stores"].items():
            services = store["services"]

            properties = {
                "ref": store["cost_center"],
                "name": store["display_brand"],
                "addr_full": store["address"],
                "city": store["city"],
                "country": store["country"],
                "lat": re.sub(r"[^\d\-\.]", "", store["latitude"]),
                "lon": re.sub(r"[^\d\-\.]", "", store["longitude"]),
                "website": f"https://www.circlek.com{store['url']}"
                if store["url"]
                else None,
                "brand": store["display_brand"],
                "brand_wikidata": WIKIBRANDS.get(
                    store["display_brand"], WIKIBRANDS["Circle K"]
                ),
                "extras": {
                    "amenity:fuel": any("gas" == s["name"] for s in services) or None,
                    "fuel:diesel": any("diesel" == s["name"] for s in services) or None,
                    "car_wash": any("car_wash" == s["name"] for s in services) or None,
                    "shop": "convenience",
                },
            }

            yield scrapy.Request(
                url=response.urljoin(store["url"]),
                callback=self.parse_state,
                meta={"properties": properties},
            )

    def parse_state(self, response):
        properties = response.meta["properties"]
        # Not all countries/store pages follow the same format
        if properties["country"] == "US":
            state = response.xpath(
                '//*[@class="heading-small"]/span[2]/text()'
            ).extract_first()
            postal = response.xpath(
                '//*[@class="heading-small"]/span[3]/text()'
            ).extract_first()
        elif properties["country"] in ["CA", "Canada"]:
            extracted = response.xpath(
                '//*[@class="heading-small"]/span[2]/text()'
            ).extract_first()
            if extracted and len(extracted) < 4:
                state = response.xpath(
                    '//*[@class="heading-small"]/span[2]/text()'
                ).extract_first()
                postal = response.xpath(
                    '//*[@class="heading-small"]/span[3]/text()'
                ).extract_first()
            else:
                state = ""
                postal = response.xpath(
                    '//*[@class="heading-small"]/span[2]/text()'
                ).extract_first()
        else:
            state = ""
            postal = response.xpath(
                '//*[@class="heading-small"]/span[2]/text()'
            ).extract_first()

        properties.update(
            {
                "state": state,
                "postcode": postal,
            }
        )

        yield GeojsonPointItem(**properties)
