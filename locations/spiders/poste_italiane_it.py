import re

from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


def add_it_ranges(oh, string):
    oh.add_ranges_from_string(
        string,
        days=DAYS_IT,
        named_day_ranges=NAMED_DAY_RANGES_IT,
        named_times=NAMED_TIMES_IT,
        closed=CLOSED_IT,
        delimiters=DELIMITERS_IT,
    )


class PosteItalianeITSpider(JSONBlobSpider):
    name = "poste_italiane_it"
    # web page: https://www.poste.it/cerca/index.html#/vieni-in-poste
    # if grouped differently, they group separate but near points losing information
    point_groups = [
        ["UfficioPostale", "PuntoPoste", "PuntoPosteLocker"],
        ["CassettaPostale", "SpazioFilatelico"],
        ["Merchant"],
    ]
    locations_key = ["data", "listaPunti"]
    POSTE_BRAND = {"brand": "Poste Italiane", "brand_wikidata": "Q495026"}
    PUNTO_POSTE_BRAND = {
        "post_office:brand": "Poste Italiane",
        "post_office:brand:wikidata": "Q495026",
    }
    TOBACCO_MATCH = re.compile(r"^Tabacc[a-z]+\s*(?:N\.\s*)?(\d+)?(?:$|\s+)", re.I)
    merchant_types = {
        "ABBIGLIAMENTO": Categories.SHOP_CLOTHES,
        "CARBURANTE": Categories.FUEL_STATION,
        "SPESA_E_CUCINA": Categories.SHOP_SUPERMARKET,
    }

    def start_requests(self):
        for group in self.point_groups:
            yield JsonRequest(
                "https://mapcollection.poste.it/v2/map/geoList",
                data={
                    "lon": 12.480178129359274,
                    "lat": 41.89637400808064,
                    "spanLon": 7,
                    "spanLat": 7,
                    "tipoPunto": group,
                    "limit": 100000,
                },
                meta={"download_timeout": 30},
            )

    def pre_process_data(self, location):
        location["indirizzo"] = location.get("indirizzoPunto")
        location["name"] = location.get("nomePunto")
        location["phone"] = location.get("numeroTelefono")

    def post_process_item(self, item, response, location):
        tipo = location["tipoPunto"]
        if tipo == "UfficioPostale":
            self.post_process_ufficio_postale(item, location)
        elif tipo == "SpazioFilatelico":
            self.post_process_spazio_filatelico(item, location)
        elif tipo == "PuntoPoste":
            self.post_process_punto_poste(item, location)
        elif tipo == "PuntoPosteLocker":
            apply_category(Categories.PARCEL_LOCKER, item)
            item.update(self.POSTE_BRAND)
            self.apply_hours(item, location["orari"])
        elif tipo == "CassettaPostale":
            self.post_process_cassetta_postale(item, location)
        elif tipo == "Merchant":
            self.post_process_merchant(item, location)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_type/{tipo}")
        if fax := location.get("fax"):
            item["extras"]["contact:fax"] = fax
        yield item

    def post_process_ufficio_postale(self, item, location):
        item["branch"] = item["name"]
        item["name"] = f'Ufficio Postale {item["branch"]}'
        item.update(self.POSTE_BRAND)
        apply_category(Categories.POST_OFFICE, item)
        self.apply_hours(item, location["orari"])
        for s in location["servizi"]:
            apply_yes_no(Extras.WIFI, item, s["codice"] == "WIFI")
            apply_yes_no(Extras.ATM, item, s["codice"] == "ATMNONH24")
            apply_yes_no(Extras.ATM, item, s["codice"] == "ATMH24")

    def post_process_spazio_filatelico(self, item, location):
        item.update(self.POSTE_BRAND)
        apply_category(Categories.SHOP_COLLECTOR, item)
        item["extras"]["collector"] = "coins;medals;postcards;stamps"
        self.apply_hours(item, location["orari"])

    def post_process_punto_poste(self, item, location):
        apply_category(Categories.POST_PARTNER, item)
        item["extras"].update(self.PUNTO_POSTE_BRAND)
        item["extras"]["ref:poste_italiane"] = item["ref"]
        self.apply_hours(item, location.get("orariPuntoPoste"))
        if ref := self.TOBACCO_MATCH.findall(item["name"]):
            apply_category(Categories.SHOP_TOBACCO, item)
            item["extras"]["ref:tobacco"] = ref[0]

    def post_process_cassetta_postale(self, item, location):
        apply_category(Categories.POST_BOX, item)
        item["extras"]["ref:poste_italiane"] = item["ref"]
        item["ref"] = item.pop("name")
        item.update(self.POSTE_BRAND)
        if coll := location.get("orarioVuotatura"):
            if "," in coll:
                days = coll.split(",")
                h = days[-1].split(" ")[-1]
                days[-1] = days[-1].strip().split(" ")[0]
                item["extras"]["collection_times"] = (
                    ",".join(map(lambda day: DAYS_IT[day.strip().title()], days)) + " " + h
                )
            else:
                oh = OpeningHours()
                add_it_ranges(oh, f"{coll} - {coll[-5:]}")
                item["extras"]["collection_times"] = oh.as_opening_hours()[:-6]
            # self.crawler.stats.inc_value(f"atp/{self.name}/collection_times/{coll}")
            # self.crawler.stats.inc_value(f"atp/{self.name}/collection_times/{item['extras']['collection_times']}")
        else:
            item["extras"]["collection_times:signed"] = "no"

    def post_process_merchant(self, item, location):
        item["extras"]["ref:vatin"] = "IT" + location["partitaIva"]
        apply_yes_no(PaymentMethods.BANCOPOSTA, item, True)
        apply_yes_no(PaymentMethods.POSTEPAY, item, True)
        codice = location["categoriaMerchant"]["codice"]
        if category := self.merchant_types.get(codice):
            apply_category(category, item)
        elif ref := self.TOBACCO_MATCH.findall(item.get("name") or ""):
            apply_category(Categories.SHOP_TOBACCO, item)
            item["extras"]["ref:tobacco"] = ref[0]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_merchant/{codice}")

    def apply_hours(self, item, list_h):
        if not list_h:
            return
        oh = OpeningHours()
        for day_h in list_h:
            day = day_h["giorno"]
            hour = day_h["orario"]
            add_it_ranges(oh, f"{day}: {hour}")
        item["opening_hours"] = oh
