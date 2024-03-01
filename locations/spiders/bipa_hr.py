from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.hours import DAYS_SR, OpeningHours
from locations.items import Feature


class BipaHRSpider(Spider):
    name = "bipa_hr"
    item_attributes = {
        "brand": "Bipa",
        "brand_wikidata": "Q864933",
    }

    def start_requests(self):
        yield JsonRequest(
            "https://www.bipa.hr/api/2sxc/app/auto/query/SvePoslovnice/Poslovnice",
            headers={
                "ModuleId": "841",
                "TabId": "195",
            },
        )

    def parse(self, response: Response):
        for store in response.json()["Poslovnice"]:
            opening_hours = OpeningHours()
            opening_hours.add_ranges_from_string(store["RadnoVrijeme"], days=DAYS_SR)

            yield Feature(
                ref=store["Id"],
                city=store["Grad"],
                street_address=store["Adresa"],
                postcode=store["PPbroj"],
                phone=store["Telefon"],
                state=store["Regija"],
                lat=store["Longitude"],
                lon=store["Latitude"],
                opening_hours=opening_hours,
            )
