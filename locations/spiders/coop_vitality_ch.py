import re

import scrapy

from locations.items import Feature


class CoopVitalityCHSpider(scrapy.Spider):
    name = "coop_vitality_ch"
    item_attributes = {"brand": "Coop Vitality", "brand_wikidata": "Q111725297"}
    allowed_domains = ["www.coopvitality.ch"]
    start_urls = ("https://www.coopvitality.ch/de/storepickup/index/loadstore/",)

    def parse(self, response):
        for s in response.json()["storesjson"]:
            properties = {
                "email": s.get("email"),
                "image": self.parse_image(s),
                "lat": s["latitude"],
                "lon": s["longitude"],
                "phone": s.get("phone").replace(" ", ""),
                "ref": s["galenicare_pharmacy_number"],
                "website": self.parse_website(s),
                "branch": s.get("store_name", "").replace("Coop Vitality", "").strip(),
            }
            properties.update(self.parse_addr(s))
            properties.update(self.parse_addr(s))
            properties = {k: v for (k, v) in properties.items() if v}
            yield Feature(**properties)

    def parse_addr(self, s):
        located_in, street, housenumber = s.get("address"), s.get("address_2"), ""
        if not street:
            p = located_in.split(",", 1)
            located_in, street = p if len(p) == 2 else (None, p[0])
        m = re.search(r"^\s*(.+?)\s+([0-9]+[A-Za-z]?)$", street)
        if m is not None:
            street, housenumber = m.group(1), m.group(2)
        if located_in in {"Allée du Communet", "Beim Neumarkt 4"}:
            located_in = None
        located_in_wikidata = {
            "Einkaufszentrum Letzipark": "Q1489092",
            "Pilatusmarkt": "Q2094879",
            "Sihlcity": "Q1703434",
        }.get(located_in)
        return {
            "city": s.get("city"),
            "country": "CH",
            "housenumber": housenumber.strip().lower(),
            "located_in": located_in,
            "located_in_wikidata": located_in_wikidata,
            "postcode": s.get("zipcode"),
            "street": street,
        }

    def parse_image(self, s):
        baseimage = s.get("baseimage", "").replace(r"\/", "/")
        if baseimage:
            return "https://www.coopvitality.ch/media/%s" % baseimage
        else:
            return None

    def parse_website(self, s):
        path = s["rewrite_request_path"]
        postcode = int(s["zipcode"])
        if postcode <= 2499 or postcode >= 2800 and postcode <= 2999:
            lang = "fr"
        elif postcode >= 6500 and postcode <= 6999:
            lang = "it"
        else:
            lang = "de"
        return "https://www.coopvitality.ch/%s/%s" % (lang, path)
