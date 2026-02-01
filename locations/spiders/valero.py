from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class ValeroSpider(Spider):
    name = "valero"
    item_attributes = {"brand": "Valero", "brand_wikidata": "Q1283291"}
    allowed_domains = ["valero.com"]
    usa_bbox = [-125, 24, -65, 51]
    xstep = 5
    ystep = 3
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_search(self, xmin: int, ymin: int, xmax: int, ymax: int) -> FormRequest:
        return FormRequest(
            "https://locations.valero.com/en-us/Home/SearchForLocations",
            formdata={
                "NEBound_Lat": str(ymax),
                "NEBound_Long": str(xmax),
                "SWBound_Lat": str(ymin),
                "SWBound_Long": str(xmin),
            },
            meta={
                "dont_redirect": True,
            },
        )

    async def start(self) -> AsyncIterator[FormRequest]:
        xs = list(range(self.usa_bbox[0], self.usa_bbox[2] + self.xstep, self.xstep))
        ys = list(range(self.usa_bbox[1], self.usa_bbox[3] + self.ystep, self.ystep))
        for xmin, xmax in zip(xs, xs[1:]):
            for ymin, ymax in zip(ys, ys[1:]):
                yield self.make_search(xmin, ymin, xmax, ymax)

    def parse(self, response):
        for row in response.json():
            amenities = [detail["Description"] for detail in row["LocationDetails"]]
            website = (
                f"https://locations.valero.com/en-us/LocationDetails/Index/{row['DetailPageUrlID']}/{row['LocationID']}"
            )
            item = {
                "ref": row["LocationID"],
                "lat": row["Latitude"],
                "lon": row["Longitude"],
                "name": row["Name"],
                "phone": row["Phone"],
                "website": website,
                "street_address": row["AddressLine1"],
                "city": row["City"],
                "state": row["State"],
                "country": row["Country"],
                "postcode": row["PostalCode"],
                "opening_hours": "24/7" if "24 Hour" in amenities else None,
            }

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.ATM, item, "ATM" in amenities)
            apply_yes_no(Extras.TOILETS, item, "Public Restroom" in amenities)
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in amenities)
            apply_yes_no(Fuel.DIESEL, item, "Diesel" in amenities)
            apply_yes_no(Fuel.E85, item, "E-85" in amenities)

            yield Feature(**item)
