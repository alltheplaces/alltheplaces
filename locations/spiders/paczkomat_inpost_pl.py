import re

from scrapy import Spider
from unidecode import unidecode

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class PaczkomatInpostPLSpider(Spider):
    name = "paczkomat_inpost_pl"
    brands = {
        "paczkomat": {"brand": "Paczkomat InPost", "brand_wikidata": "Q110970254"},
        "appkomat": {
            "brand": "Appkomat InPost",
            "brand_wikidata": "",
            "extras": {"app_operated": "only", "not:brand:wikidata": "Q110970254", "amenity": "parcel_locker"},
        },
    }

    item_attributes = {"brand": "Paczkomat InPost", "brand_wikidata": "Q110970254"}
    allowed_domains = ["inpost.pl"]
    start_urls = ["https://inpost.pl/sites/default/files/points.json"]

    def parse(self, response, **kwargs):
        for poi in response.json()["items"]:
            # Skip non-active locations and places which are not parcel lockers
            if poi["s"] != 1 and poi["t"] != 1 or poi["n"].startswith("POP-") or poi["c"] == "system":
                continue

            item = Feature()
            # The mapping is available in "load" js function of inpostLocatorMap object

            item["ref"] = poi["n"]

            if item["ref"].endswith("APP"):
                item.update(self.brands["appkomat"])
            else:
                item.update(self.brands["paczkomat"])

            item["extras"]["description"] = poi["d"]
            item["city"] = poi["c"]
            if "/" not in poi["e"]:
                item["street"] = poi["e"].removeprefix("ul.").removesuffix(poi["b"]).replace("-go", "").strip()
                item["street"] = item["street"][:1].upper() + item["street"][1:]
                if item["street"].startswith("Al."):
                    item["street"] = "Aleja " + item["street"][3:].strip()
                if item["street"].startswith("Gen."):
                    item["street"] = "Generała " + item["street"][4:].strip()
                if item["street"].startswith("Ks."):
                    item["street"] = "Księdza " + item["street"][3:].strip()
                if item["street"].startswith("Os.") or item["street"].startswith("Oś."):
                    item["street"] = "Osiedle " + item["street"][3:].strip()
                if item["street"].startswith("Płk."):
                    item["street"] = "Pułkownika " + item["street"][4:].strip()
                if item["street"].startswith("Pl."):
                    item["street"] = "Plac " + item["street"][3:].strip()
                if item["street"].startswith("Plac ") or item["street"].startswith("Osiedle "):
                    item["extras"]["addr:place"] = item["street"]
                    item["street"] = ""
                if item["street"] == item["city"]:
                    item["extras"]["addr:place"] = item["city"]
                    item["city"] = ""
                    item["street"] = ""
            item["postcode"] = poi["o"]
            if poi["b"].lower() not in ["b/n", "bn", "b.n", "b.n.", "bn.", "brak numeru", "n/n"]:
                item["housenumber"] = poi["b"]
            item["lat"] = poi["l"]["a"]
            item["lon"] = poi["l"]["o"]

            item["image"] = f'https://geowidget.easypack24.net/uploads/pl/images/{item["ref"]}.jpg'

            # TODO: figure out if below could be mapped
            # poi["m"]  # apm_doubled
            # poi["q"]  # partner_id
            # poi["f"]  # physical_type_mapped
            # poi["g"]
            # poi["p"]  # payment

            item["website"] = f'https://inpost.pl/{self.parse_slug(item, poi["e"], poi["r"])}'
            if poi["h"] == "24/7":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(poi["h"], days=DAYS_PL)
            yield item

    def parse_slug(self, item, street, state):
        slug_parts = ["paczkomat", item["city"], item["ref"], street, "paczkomaty", state]
        slug = "-".join(map(lambda x: unidecode(x.lower().strip()), slug_parts))
        slug = re.sub(r"[·/_:; ]", "-", slug)
        slug = re.sub(r"[^a-z0-9 -]", "", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug
