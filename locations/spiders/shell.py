import scrapy

from locations.items import GeojsonPointItem
from locations.spiders.costacoffee_gb import yes_or_no


class ShellSpider(scrapy.Spider):
    name = "shell"
    item_attributes = {"brand": "Shell", "brand_wikidata": "Q110716465"}
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
                    yield scrapy.Request(f"https://shellgsllocator.geoapp.me/api/v1/locations/{item['id']}")
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
                    "amenity:chargingstation": yes_or_no(
                        "electric_charging_other" in fuels or "shell_recharge" in fuels
                    ),
                    "amenity": "fuel",
                    "toilets": yes_or_no("toilet" in amenities),
                    "atm": yes_or_no("atm" in amenities),
                    "car_wash": yes_or_no("carwash" in amenities),
                    "fuel:adblue": yes_or_no(any("adblue" in a for a in amenities)),
                    "fuel:biodiesel": yes_or_no("biodiesel" in fuels or "biofuel_gasoline" in fuels),
                    "fuel:cng": yes_or_no("cng" in fuels),
                    "fuel:diesel": yes_or_no(any("diesel" in f for f in fuels)),
                    "fuel:GTL_diesel": yes_or_no("gtl" in fuels),
                    "fuel:HGV_diesel": yes_or_no("truck_diesel" in fuels or "hgv_lane" in amenities),
                    "fuel:LH2": yes_or_no("hydrogen" in fuels),
                    "fuel:lng": yes_or_no("lng" in fuels),
                    "fuel:lpg": yes_or_no("autogas_lpg" in fuels),
                    "fuel:octane_100": yes_or_no("super_premium_gasoline" in fuels),
                    # definition of low-octane varies by country; 92 is most common
                    "fuel:octane_92": yes_or_no("low_octane_gasoline" in fuels),
                    # definition of mid-octane varies by country; 95 is most common
                    "fuel:octane_95": yes_or_no(
                        any("midgrade_gasoline" in f for f in fuels) or "unleaded_super" in fuels
                    ),
                    # the US region seems to also use 'premium_gasoline' to refer to non-diesel gas products
                    "fuel:octane_98": yes_or_no(any("98" in f for f in fuels) or "premium_gasoline" in fuels),
                    "fuel:propane": yes_or_no("auto_rv_propane" in fuels),
                    "hgv": yes_or_no("hgv_lane" in amenities),
                    "shop": "convenience" if "shop" in "amenities" else "no",
                    "wheelchair": yes_or_no("disabled_facilities" in amenities),
                },
            )
