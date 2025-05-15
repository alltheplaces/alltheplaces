import itertools
import re
from urllib.parse import urlparse

import scrapy
from parsel import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature

# “Ich tanke Strom“, charging stations for electric vehicles.
# Published as Open Data by the Swiss Federal Office of Energy.
#
# https://ich-tanke-strom.ch/
# https://opendata.swiss/en/dataset/ladestationen-fuer-elektroautos
#
# Most charging stations are located in Switzerland, but the data feed
# also includes a small number of stations in various other countries,
# such as Israel or Laos, if they happen to be owned or operated by
# Swiss companies. In particular, there is one Swiss start-up that
# manufactures do-it-yourself kits for charging stations and sells
# them around the world; their customers become part of a global,
# public charging network. The Swiss company then submits its (global)
# charging station locations to the Swiss Federal Office of Energy,
# which aggregates them it with all other data from Swiss companies,
# and publishes the result as a single data feed.


class IchTankeStromSpider(scrapy.Spider):
    name = "ich_tanke_strom"
    allowed_domains = ["data.geo.admin.ch"]
    start_urls = (
        "https://data.geo.admin.ch/ch.bfe.ladestellen-elektromobilitaet/data/ch.bfe.ladestellen-elektromobilitaet_de.json",
    )

    # TODO: Add missing rules to NSI, at least for the larger operators.
    operators = {
        "ail.ch": ("Aziende Industriali di Lugano", "Q3631473"),
        "ckw.ch": ("Centralschweizerische Kraftwerke", "Q1054107"),
        "deviwa.ch": ("Deviwa", "Q115241817"),
        "ecarup.com": ("eCarUp", "Q113192759"),
        "energieuri.ch": ("Energie Uri", "Q115242162"),
        "eniwa.ch": ("Eniwa", "Q28500440"),
        "evpass.ch": ("EVPass", "Q113270804"),
        "ewd.ch": ("Elektrizitätswerk Davos", "Q115232332"),
        "ewo.ch": ("Elektrizitätswerk Obwalden", "Q22920309"),
        "herrliberg.ch": ("Gemeinde Herrliberg", "Q69224"),
        "lidl.ch": ("Lidl", "Q151954"),
        "migrol.ch": ("Migrol", "Q1747771"),
        "mobilecharge.ch": ("mobilecharge", "Q115241641"),
        "move.ch": ("Move", "Q110278557"),
        "parkandcharge.ch": ("EW Höfe", "Q115242292"),
        "plugnroll.com": ("Plug’n Roll", "Q115241443"),
        "swisscharge.ch": ("Swisscharge", "Q113162249"),
        "tesla.com": ("Tesla, Inc.", "Q478214"),
    }

    brands = {
        "tesla.com": ("Tesla Supercharger", "Q17089620"),
    }

    def parse(self, response):
        feed = response.json()
        for f in feed["features"]:
            lon, lat = f["geometry"]["coordinates"]
            html = Selector(f["properties"]["description"])
            tags = {"access": self.parse_access(html)}
            tags.update(self.parse_operator(html))
            tags.update(self.parse_socket(html))
            properties = {
                "brand": tags.pop("brand", None),
                "brand_wikidata": tags.pop("brand:wikidata", None),
                "operator": tags.pop("operator", None),
                "operator_wikidata": tags.pop("operator:wikidata", None),
                "extras": tags,
                "lat": lat,
                "lon": lon,
                "ref": f["id"],
            }
            properties.update(self.parse_address(html))
            apply_category(Categories.CHARGING_STATION, properties)
            yield Feature(**properties)

    def parse_access(self, html):
        # Occasionally, the feed gives multiple access restrictions.
        # Perhaps not all sockets are equal, or perhaps it’s a data error.
        # We simply convert the input we’ve received.
        access_types = {
            "Keine Angabe": "unknown",
            "Eingeschränkt zugänglich": "limited",
            "Öffentlich zugänglich": "permissive",
        }
        m = html.xpath("(//td[text()='Zugang']/../td)[2]/text()").get()
        access = {access_types.get(s.strip()) for s in m.split(",")}
        return ";".join(sorted([a for a in access if a]))

    def parse_address(self, html):
        if td := html.xpath("(//td[text()='Standort']/../td)[2]/text()").get():
            addr_full = " ".join(td.split())
            return {"addr_full": addr_full}
        else:
            return {}

    def parse_operator(self, html):
        # In the data feed, none of the websites are specific to a single
        # charging station; it’s always the operator website.
        td = html.xpath("//td[text()='Ladenetzwerk']/../td")
        operator_website = td.xpath("a/@href").get()
        domain = urlparse(operator_website).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        operator, operator_wikidata = self.operators.get(domain, (None, None))
        brand, brand_wikidata = self.brands.get(domain, (None, None))
        if not operator:
            operator = td.xpath("a/text()").get()
        return {
            "brand": brand,
            "brand:wikidata": brand_wikidata,
            "operator": operator,
            "operator:website": operator_website,
            "operator:wikidata": operator_wikidata,
        }

    def parse_socket(self, html):
        # https://wiki.openstreetmap.org/wiki/Key:socket
        socket_types = {
            "CCS": "type2_combo",
            "CHAdeMO": "chademo",
            "Haushaltsteckdose CH": "sev1011_t13",
            "Haushaltsteckdose Schuko": "schuko",
            "IEC 60309": "cee_blue",
            "Kabel Typ 1": "type1_cable",
            "Kabel Typ 2": "type2_cable",
            "Steckdose Typ 2": "type2",
            "Steckdose Typ 3": "type3",
            "Tesla": "tesla_supercharger",
        }

        m = html.css(".evse-overview").xpath("//tr/td/text()")
        t = [s.strip() for s in m.getall()]

        # Collect type and power output (in kilowatts) of available sockets
        # into a dict like {"type2": [22.0, 22.0], "type2_combo": [50.0]}.
        sockets = {}
        for key, val in itertools.pairwise(t):
            if socket := socket_types.get(key):
                if m := re.search(r"([0-9\.]+)\s*kW", val):
                    power = float(m.group(1))
                    sockets.setdefault(socket, []).append(power)

        # Return OSM tags like `socket:type2=2` and `socket:type2:output=22.0 kW`.
        # https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dcharging_station
        tags = {}
        for socket, power in sockets.items():
            tags["socket:%s" % socket] = len(power)
            tags["socket:%s:output" % socket] = "%s kW" % max(power)
        return tags
