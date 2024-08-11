import scrapy
from scrapy.http.request import Request

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class SparAspiagSpider(scrapy.Spider):
    # Spar stores run by ASPIAG: https://www.aspiag.com/en/countries
    # See also https://github.com/alltheplaces/alltheplaces/pull/9379
    name = "spar_aspiag"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}

    COUNTRIES = [
        {
            "country_code": "SI",
            "domain": "www.spar.si",
            "path": "trgovine",
            "days": ("ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja"),
        },
        {
            "country_code": "HR",
            "domain": "www.spar.hr",
            "path": "lokacije",
            "days": (
                "ponedjeljak",
                "utorak",
                "srijeda",
                "četvrtak",
                "petak",
                "subota",
                "nedjelja",
            ),
        },
        {
            "country_code": "AT",
            "domain": "www.spar.at",
            "path": "standorte",
            "days": (
                "montag",
                "dienstag",
                "mittwoch",
                "donnerstag",
                "freitag",
                "samstag",
                "sonntag",
            ),
        },
        {
            "country_code": "HU",
            "domain": "www.spar.hu",
            "path": "uzletek",
            "days": ("hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"),
        },
    ]

    allowed_domains = [c["domain"] for c in COUNTRIES]

    def start_requests(self):
        for config in self.COUNTRIES:
            yield Request(
                f'https://{config["domain"]}/{config["path"]}/_jcr_content.stores.v2.html',
                cb_kwargs=dict(
                    config=config,
                ),
            )

    def parse(self, response, config):
        for row in response.json():
            feature = Feature(
                ref=row["locationId"],
                name=row["name"],
                phone=row["telephone"],
                lat=row["latitude"],
                lon=row["longitude"],
                street_address=row["address"],
                postcode=row["zipCode"],
                city=row["city"],
                website=f'https://{config["domain"]}' + row["pageUrl"],
                country=config["country_code"],
                opening_hours=self.parse_open_hours(row["shopHours"], config["days"]) or None,
            )

            name_lower = row["name"].lower()
            if name_lower.startswith("eurospar") or name_lower.startswith("interspar"):
                apply_category(Categories.SHOP_SUPERMARKET, feature)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, feature)
            yield feature

    def parse_open_hours(self, hours, days: list):
        opening_hours = OpeningHours()
        for interval in hours:
            dow_i = days.index(interval["openingHours"]["dayType"].lower())
            day = DAYS[dow_i]

            if interval["openingHours"]["from1"]:
                opening_hours.add_range(
                    day=day,
                    open_time=f'{interval["openingHours"]["from1"]["hourOfDay"]}:{interval["openingHours"]["from1"]["minute"]}',
                    close_time=f'{interval["openingHours"]["to1"]["hourOfDay"]}:{interval["openingHours"]["to1"]["minute"]}',
                )

            if interval["openingHours"]["from2"]:
                opening_hours.add_range(
                    day=day,
                    open_time=f'{interval["openingHours"]["from2"]["hourOfDay"]}:{interval["openingHours"]["from2"]["minute"]}',
                    close_time=f'{interval["openingHours"]["to2"]["hourOfDay"]}:{interval["openingHours"]["to2"]["minute"]}',
                )

        return opening_hours.as_opening_hours()
