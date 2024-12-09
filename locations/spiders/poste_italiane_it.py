import re

from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class PosteItalianeITSpider(JSONBlobSpider):
    name = "poste_italiane_it"
    # web page: https://www.poste.it/cerca/index.html#/vieni-in-poste
    start_urls = ["https://mapcollection.poste.it/v2/map/geoList"]
    locations_key = ["data", "listaPunti"]
    POSTE_BRAND = {"brand": "Poste Italiane", "brand_wikidata": "Q495026"}
    PUNTO_POSTE_BRAND = {
        "post_office:brand": "Poste Italiane",
        "post_office:brand:wikidata": "Q495026",
    }
    TOBACCO_MATCH = re.compile(r"^Tabacc.+\s*N\.\s*(\d+)$")

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url,
                data={
                    "lon": 12.480178129359274,
                    "lat": 41.89637400808064,
                    "spanLon": 7,
                    "spanLat": 7,
                    "tipoPunto": ["UfficioPostale", "PuntoPoste", "PuntoPosteLocker"],
                    "limit": 100000,
                },
                meta={"download_timeout": 30},
            )

    def pre_process_data(self, location):
        location["indirizzo"] = location.pop("indirizzoPunto")
        location["name"] = location.pop("nomePunto")
        location["phone"] = location.get("numeroTelefono")

    def post_process_item(self, item, response, location):
        if location["tipoPunto"] == "UfficioPostale":
            item["branch"] = item["name"]
            item["name"] = f'Ufficio Postale {item["branch"]}'
            item.update(self.POSTE_BRAND)
            apply_category(Categories.POST_OFFICE, item)
            self.apply_hours(item, location["orari"])
            for s in location["servizi"]:
                apply_yes_no(Extras.WIFI, item, s["codice"] == "WIFI")
                apply_yes_no(Extras.ATM, item, s["codice"] == "ATMNONH24")
                apply_yes_no(Extras.ATM, item, s["codice"] == "ATMH24")
        elif location["tipoPunto"] == "PuntoPoste":
            apply_category(Categories.POST_PARTNER, item)
            item["extras"].update(self.PUNTO_POSTE_BRAND)
            item["extras"]["ref:poste_italiane"] = item["ref"]
            self.apply_hours(item, location.get("orariPuntoPoste"))
            if ref := self.TOBACCO_MATCH.findall(item["name"]):
                apply_category(Categories.SHOP_TOBACCO, item)
                item["extras"]["ref:tobacco"] = ref[0]
        elif location["tipoPunto"] == "PuntoPosteLocker":
            apply_category(Categories.PARCEL_LOCKER, item)
            item.update(self.POSTE_BRAND)
            self.apply_hours(item, location["orari"])
        if fax := location.get("fax"):
            item["extras"]["contact:fax"] = fax
        yield item

    def apply_hours(self, item, list_h):
        if not list_h:
            return
        oh = OpeningHours()
        for day_h in list_h:
            day = day_h["giorno"]
            hour = day_h["orario"]
            oh.add_ranges_from_string(
                f"{day}: {hour}",
                days=DAYS_IT,
                named_day_ranges=NAMED_DAY_RANGES_IT,
                named_times=NAMED_TIMES_IT,
                closed=CLOSED_IT,
                delimiters=DELIMITERS_IT,
            )
        item["opening_hours"] = oh
