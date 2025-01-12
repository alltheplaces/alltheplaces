from unidecode import unidecode

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL

from .inpost_it import InpostITSpider


class PaczkomatInpostPLSpider(InpostITSpider):
    name = "paczkomat_inpost_pl"
    allowed_domains = ["inpost.pl"]

    brand_locker = {"brand": "Paczkomat InPost", "brand_wikidata": "Q110970254", "nsi_id": "paczkomatinpost-ce4e28"}
    brand_partner = {"post_office:brand": "Paczkomat InPost", "post_office:brand:wikidata": "Q110970254"}
    brand_app = {"brand": "Appkomat InPost", "nsi_id": "appkomatinpost-ce4e28"}
    brand_app_attributes = {"app_operated": "only", "not:brand:wikidata": "Q110970254", "amenity": "parcel_locker"}

    def set_brand(self, item, location):
        if item["ref"].endswith("APP"):
            if location["category"] != Categories.PARCEL_LOCKER:
                raise ValueError("Appkomat only expected for lockers")
            item.update(self.brand_app)
            apply_category(self.brand_app_attributes, item)
        else:
            super().set_brand(item, location)

    def parse_hours(self, oh, hours):
        oh.add_ranges_from_string(hours, days=DAYS_PL)

    def slug_parts(self, item, location):
        ref = item["ref"]
        city = unidecode(item["city"])
        street = unidecode(item["street"])
        state = unidecode(item["state"])
        if location["category"] == Categories.PARCEL_LOCKER:
            return ["paczkomat", city, ref, street, "paczkomaty", state]
        else:
            return ["punkt-obslugi-paczek", ref, city, street]

    def post_process_locker(self, item, location):
        item["extras"]["description"] = item["name"]
        item["name"] = None
        self.add_image(item)
        yield item

    def post_process_partner(self, item, location):
        self.add_image(item)
        yield item

    def add_image(self, item):
        item["image"] = f'https://geowidget.easypack24.net/uploads/pl/images/{item["ref"]}.jpg'

    def clean_address(self, item, poi):
        item["addr_full"] = [
            f'{item["street"]} {item["housenumber"]}',
            f'{item["city"]} {item["postcode"]}',
        ]
        if "/" not in item["street"]:
            item["street"] = (
                item["street"].removeprefix("ul.").removesuffix(item["housenumber"] or "").replace("-go", "").strip()
            )
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
        if item["housenumber"]:
            if item["housenumber"].lower() in [
                "b/n",
                "bn",
                "b.n",
                "b.n.",
                "bn.",
                "brak numeru",
                "n/n",
            ]:
                item["housenumber"] = None
