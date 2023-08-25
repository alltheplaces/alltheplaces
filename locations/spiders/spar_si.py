import scrapy
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours

from locations.items import Feature


DAY_MAP = {
    "Ponedeljek": "Mo",
    "Torek": "Tu",
    "Sreda": "We",
    "Četrtek": "Th",
    "Petek": "Fr",
    "Sobota": "Sa",
    "Nedelja": "Su",
}

class SparSISpider(scrapy.Spider):
    name = "spar_si"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}
    INTERSPAR = {"brand": "Interspar", "brand_wikidata": "Q12309283"}

    allowed_domains = ["www.spar.si"]

    start_urls = ["https://www.spar.si/trgovine/_jcr_content.stores.v2.html"]

    def parse(self, response):
        for row in response.json():
            # TODO: handle "type"
            feature = Feature(
                ref=row["locationId"],
                name=row["name"],
                phone=row["telephone"],
                lat=row["latitude"],
                lon=row["longitude"],
                street_address=row["address"],
                postcode=row["zipCode"],
                city=row["city"],
                website="https://www.spar.si" + row["pageUrl"],
                country="SI",
                opening_hours=self.parse_open_hours(row["shopHours"]) or None,
            )
            if "Interspar" in row["name"]:
                apply_category(Categories.SHOP_SUPERMARKET, feature)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, feature)
            yield feature


    def parse_open_hours(self, hours):
        opening_hours = OpeningHours()
        for interval in hours:
            day = DAY_MAP[interval["openingHours"]["dayType"]]
            
            if interval["openingHours"]["from1"]:
                from1 = str(interval["openingHours"]["from1"]["hourOfDay"]) + ":" + str(interval["openingHours"]["from1"]["minute"])
                to1 = str(interval["openingHours"]["to1"]["hourOfDay"]) + ":" + str(interval["openingHours"]["to1"]["minute"])

                opening_hours.add_range(
                    day=day,
                    open_time=from1,
                    close_time=to1,
                )

            if interval["openingHours"]["from2"]:
                from2 = str(interval["openingHours"]["from2"]["hourOfDay"]) + ":" + str(interval["openingHours"]["from2"]["minute"])
                to2 = str(interval["openingHours"]["to2"]["hourOfDay"]) + ":" + str(interval["openingHours"]["to2"]["minute"])

                opening_hours.add_range(
                    day=day,
                    open_time=from2,
                    close_time=to2,
                )

        return opening_hours.as_opening_hours()