import re

from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


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
    TOBACCO_MATCH = re.compile(r"^Tabacc.+\s*N\.\s*(\d+)$")
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
        elif location["tipoPunto"] == "SpazioFilatelico":
            item.update(self.POSTE_BRAND)
            apply_category(Categories.SHOP_COLLECTOR, item)
            item["extras"]["collector"] = "coins;medals;postcards;stamps"
            self.apply_hours(item, location["orari"])
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
        elif location["tipoPunto"] == "CassettaPostale":
            apply_category(Categories.POST_BOX, item)
            item["extras"]["ref:poste_italiane"] = item["ref"]
            item["ref"] = item.pop("name")
            item.update(self.POSTE_BRAND)
            if coll := location.get("orarioVuotatura"):
                oh = OpeningHours()
                oh.add_ranges_from_string(
                    f"{coll} - {coll[-5:]}",
                    days=DAYS_IT,
                    named_day_ranges=NAMED_DAY_RANGES_IT,
                    named_times=NAMED_TIMES_IT,
                    closed=CLOSED_IT,
                    delimiters=DELIMITERS_IT,
                )
                item["extras"]["collection_times"] = oh.as_opening_hours()
                # self.crawler.stats.inc_value(f"atp/{self.name}/collection_times/{coll}")
                # self.crawler.stats.inc_value(f"atp/{self.name}/collection_times/{item['extras']['collection_times']}")
        elif location["tipoPunto"] == "Merchant":
            item["extras"]["ref:vatin"] = "IT" + location["partitaIva"]
            apply_yes_no(PaymentMethods.BANCOPOSTA, item, True)
            apply_yes_no(PaymentMethods.POSTEPAY, item, True)
            if category := self.merchant_types.get(location["categoriaMerchant"]["codice"]):
                apply_category(category, item)
            else:
                self.crawler.stats.inc_value(
                    f"atp/{self.name}/unknown_merchant/{location['categoriaMerchant']['codice']}"
                )
                self.crawler.stats.inc_value(
                    f"atp/{self.name}/unknown_merchant/{location['categoriaMerchant']['descrizione']}"
                )
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_type/{location['tipoPunto']}")
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
