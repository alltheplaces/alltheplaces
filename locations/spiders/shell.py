# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class ShellSpider(scrapy.Spider):
    name = "shell"
    item_attributes = {"brand": "Shell", "brand_wikidata": "Q154950"}
    allowed_domains = ["shellgsllocator.geoapp.me"]
    download_delay = 0.2
    start_urls = [
        "https://shellgsllocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D=-90&sw%5B%5D=-180&ne%5B%5D=90&ne%5B%5D=180"
    ]

    def parse(self, response):
        result = response.json()

        if isinstance(result, list):
            for item in result:
                # This within_bounds endpoint always returns an array with one of
                # two kinds of response.
                #
                # 1. An array of smaller bounding boxes with counts
                # 2. An array of station listings
                if "bounds" in item:
                    b = item["bounds"]

                    yield scrapy.Request(
                        f"https://shellgsllocator.geoapp.me/api/v1/locations/within_bounds?sw%5B%5D={b['sw'][0]}&sw%5B%5D={b['sw'][1]}&ne%5B%5D={b['ne'][0]}&ne%5B%5D={b['ne'][1]}"
                    )
                elif "name" in item:
                    yield scrapy.Request(
                        f"https://shellgsllocator.geoapp.me/api/v1/locations/{item['id']}"
                    )
        else:
            if result["inactive"]:
                return

            amenities = result["amenities"]
            fuels = result["fuels"]

            yield GeojsonPointItem(
                lat=result["lat"],
                lon=result["lng"],
                name=result["name"],
                addr_full=result["address"],
                city=result["city"],
                state=result["state"],
                postcode=result["postcode"],
                country=result["country_code"],
                opening_hours="24/7" if "twenty_four_hour" in amenities else "",
                phone=result["telephone"],
                website=result["website_url"],
                ref=result["id"],
                # Definitions extracted from https://shellgsllocator.geoapp.me/config/published/retail/prod/en_US.json?format=json
                extras={
                    "amenity:chargingstation": "electric_charging_other" in fuels
                    or "shell_recharge" in fuels,
                    "amenity:fuel": True,
                    "amenity:toilets": "toilet" in amenities,
                    "atm": "atm" in amenities,
                    "car_wash": "carwash" in amenities,
                    "fuel:adblue": any("adblue" in a for a in amenities) or None,
                    "fuel:biodiesel": "biodiesel" in fuels
                    or "biofuel_gasoline" in fuels
                    or None,
                    "fuel:cng": "cng" in fuels or None,
                    "fuel:diesel": any("diesel" in f for f in fuels) or None,
                    "fuel:GTL_diesel": "gtl" in fuels or None,
                    "fuel:HGV_diesel": "truck_diesel" in fuels
                    or "hgv_lane" in amenities
                    or None,
                    "fuel:LH2": "hydrogen" in fuels or None,
                    "fuel:lng": "lng" in fuels or None,
                    "fuel:lpg": "autogas_lpg" in fuels or None,
                    "fuel:octane_100": "super_premium_gasoline" in fuels or None,
                    # definition of low-octane varies by country; 92 is most common
                    "fuel:octane_92": "low_octane_gasoline" in fuels or None,
                    # definition of mid-octane varies by country; 95 is most common
                    "fuel:octane_95": any("midgrade_gasoline" in f for f in fuels)
                    or "unleaded_super" in fuels
                    or None,
                    # the US region seems to also use 'premium_gasoline' to refer to non-diesel gas products
                    "fuel:octane_98": any("98" in f for f in fuels)
                    or "premium_gasoline" in fuels
                    or None,
                    "fuel:propane": "auto_rv_propane" in fuels or None,
                    "hgv": "hgv_lane" in amenities,
                    "shop": "convenience" if "shop" in "amenities" else None,
                    "wheelchair": "disabled_facilities" in amenities,
                },
            )
