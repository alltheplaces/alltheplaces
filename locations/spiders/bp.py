# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem

BRANDS = {"BP": "BP", "AM": "Amoco", "ARAL Tankstelle": "Aral"}

WIKIBRANDS = {"BP": "Q152057", "AM": "Q465952", "ARAL Tankstelle": "Q565734"}


class BPSpider(scrapy.Spider):
    name = "bp"
    item_attributes = {"brand": "BP", "brand_wikidata": "Q152057"}
    allowed_domains = ["bpretaillocator.geoapp.me"]
    download_delay = 0.2
    start_urls = [
        "https://bpretaillocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D=-90&sw%5B%5D=-180&ne%5B%5D=90&ne%5B%5D=180"
    ]

    def parse(self, response):
        for result in response.json():
            # This within_bounds endpoint always returns an array with one of
            # two kinds of response.
            #
            # 1. An array of smaller bounding boxes with counts
            # 2. An array of station listings
            if "bounds" in result:
                b = result["bounds"]

                yield scrapy.Request(
                    f"https://bpretaillocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D={b['sw'][0]}&sw%5B%5D={b['sw'][1]}&ne%5B%5D={b['ne'][0]}&ne%5B%5D={b['ne'][1]}"
                )
            if "name" in result:
                products = result["products"]
                facilities = result["facilities"]

                yield GeojsonPointItem(
                    lat=result["lat"],
                    lon=result["lng"],
                    name=result["name"],
                    addr_full=result["address"],
                    city=result["city"],
                    state=result["state"],
                    postcode=result["postcode"],
                    country=result["country_code"],
                    opening_hours="24/7" if "open_24_hours" in facilities else "",
                    phone=result["telephone"],
                    website=result["website"],
                    ref=result["id"],
                    brand=BRANDS.get(result["site_brand"], BRANDS["BP"]),
                    brand_wikidata=WIKIBRANDS.get(
                        result["site_brand"], WIKIBRANDS["BP"]
                    ),
                    extras={
                        "amenity:chargingstation": "electricity" in products,
                        "amenity:fuel": True,
                        "amenity:toilets": "toilet" in facilities,
                        "atm": "cash_point" in facilities,
                        "car_wash": "car_wash" in facilities,
                        "fuel:adblue": any("ad_blue" in p for p in products) or None,
                        "fuel:diesel": any("diesel" in p for p in products) or None,
                        "fuel:disel:class2": "diesel_frost" in products or None,
                        "fuel:e10": "e10" in products or None,
                        "fuel:e5": "euro_95" in products
                        or "super_e5" in products
                        or None,
                        "fuel:GTL_diesel": any("ultimate_diesel" in p for p in products)
                        or None,
                        "fuel:HGV_diesel": "truck_diesel" in products or None,
                        "fuel:lpg": "lpg" in products or None,
                        "fuel:octane_100": any("100" in p for p in products) or None,
                        "fuel:octane_102": any("102" in p for p in products) or None,
                        "fuel:octane_91": any("premium_unlead" in p for p in products)
                        or None,
                        "fuel:octane_92": any("92" in p for p in products) or None,
                        "fuel:octane_93": any("93" in p for p in products) or None,
                        "fuel:octane_95": "unlead" in products
                        or any("unleaded_95" in p for p in products)
                        or None,
                        "fuel:octane_98": "ultimate_unleaded" in products
                        or any("98" in p for p in products)
                        or None,
                        "fuel:untaxed_diesel": "red_diesel" in products or None,
                        "hgv": any("truck" in f for f in facilities),
                        "shop": "convenience" if "shop" in facilities else "",
                        "wheelchair": "disabled_facilities" in facilities,
                        "facilities": facilities,
                        "products": products,
                    },
                )
