import scrapy

from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class HeytensSpider(scrapy.Spider):
    name = "heytens"
    item_attributes = {"brand": "Heytens", "brand_wikidata": "Q90565231"}
    country_mapping = {
        "belgique": "BE",
        "france": "FR",
        "suisse": "CH",
        "luxembourg": "LU",
    }

    def start_requests(self):
        url = "https://www.heytens.be/wp-admin/admin-ajax.php"
        point_files = "eu_centroids_40km_radius_country.csv"
        for lat, lon in point_locations(point_files, list(self.country_mapping.values())):
            t = {"secure": "a6d817664e", "action": "findMagasin", "data[lat]": lat, "data[lng]": lon}
            yield scrapy.http.FormRequest(
                url,
                self.parse,
                method="POST",
                formdata={"secure": "a6d817664e", "action": "findMagasin", "data[lat]": lat, "data[lng]": lon},
            )

    def parse(self, response):
        stores = response.json()
        for store in stores:
            ohs = store.get("horaires")
            oh = OpeningHours()
            for day_index, hours in enumerate(ohs):
                if hours == "":
                    continue
                starting_open, starting_close = hours.get("ouverture"), hours.get("ferm_midi")
                ending_open, ending_close = hours.get("ouv_midi"), hours.get("fermeture")
                if starting_close == "" and ending_open == "":
                    oh.add_range(DAYS[day_index - 1], starting_open, ending_close)
                else:
                    oh.add_range(DAYS[day_index - 1], starting_open, starting_close)
                    oh.add_range(DAYS[day_index - 1], ending_open, ending_close)
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("title"),
                    "street_address": store.get("adresse"),
                    "phone": store.get("telephone"),
                    "email": store.get("email"),
                    "country": self.country_mapping[store.get("pays")],
                    "postcode": store.get("code_postal"),
                    "city": store.get("ville"),
                    "website": store.get("link"),
                    "lat": store.get("lat"),
                    "lon": store.get("lng"),
                    "opening_hours": oh,
                }
            )
