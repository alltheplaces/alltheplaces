import json, re, scrapy
from locations.hours import DAYS_DE, OpeningHours
from locations.items import GeojsonPointItem


# Open Data of the City of Zürich, https://data.stadt-zuerich.ch/
class StadtZuerichCHSpider(scrapy.Spider):
    name = "stadt_zuerich_ch"
    allowed_domains = ["ogd.stadt-zuerich.ch"]

    operators = {
        "ERZ Entsorgung + Recycling Zürich": (
            "Entsorgung + Recycling Zürich",
            "Q1345452",
        ),
        "Grün Stadt Zürich": ("Grün Stadt Zürich", "Q1551785"),
        "Stadtpolizei": ("Stadtpolizei Zürich", "Q2327949"),
        "Tiefbauamt": ("Tiefbauamt der Stadt Zürich", "Q115267460"),
        "Umwelt- und Gesundheitsschutz": (
            "Umwelt- und Gesundheitsschutz Zürich",
            "Q115271935",
        ),
    }

    url_pattern = (
        "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/%s"
        "?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON"
        "&typename=%s"
    )

    start_urls = [
        url_pattern % ("Park", "poi_park_view"),
        url_pattern % ("Sammelstelle", "poi_sammelstelle_view"),
        url_pattern % ("Stadtpolizei", "poi_stadtpolizei_view"),
        url_pattern % ("Zueri_WC", "poi_zueriwc_rs_view"),
        url_pattern % ("Zweiradparkierung", "zweiradabstellplaetze_p"),
    ]

    def parse(self, response):
        for f in response.json()["features"]:
            if item := self.parse_item(f):
                yield item

    def parse_item(self, f):
        props = f["properties"]
        coords = f["geometry"]["coordinates"]
        # Sometimes we get 3 coordinates, but the z value is always zero.
        lon, lat = coords[0], coords[1]
        id = f["id"]
        (operator, operator_wikidata) = self.operators.get(
            props.get("da"), (None, None)
        )
        tags = {
            "email": props.get("mail"),
            "name": self.parse_name(props),
            "note": self.parse_note(props),
            "opening_hours": self.parse_opening_hours(props),
            "operator": operator,
            "operator:wikidata": operator_wikidata,
            "ref": props.get("poi_id"),
            "website": props.get("www"),
            "phone": self.parse_phone(props),
        }
        tags.update(self.parse_access(props))
        tags.update(self.parse_address(props))

        # The type-specific parsers should come after the general ones,
        # so they can overwrite tags.
        if parser := {
            "poi_park_view": self.parse_park,
            "poi_sammelstelle_view": self.parse_recycling,
            "poi_stadtpolizei_view": self.parse_police,
            "poi_zueriwc_rs_view": self.parse_toilets,
            "zweiradabstellplaetze_p": self.parse_bicycle_parking,
        }.get(id.split(".")[0]):
            tags.update(parser(props))

        item = {
            "addr_full": tags.pop("addr:full", None),
            "lat": lat,
            "lon": lon,
            "city": "Zürich",
            "country": "CH",
            "email": tags.pop("email", None),
            "housenumber": tags.pop("addr:housenumber", None),
            "name": tags.pop("name", None),
            "opening_hours": tags.pop("opening_hours", None),
            "postcode": tags.pop("addr:postcode", None),
            "ref": tags.pop("ref"),
            "street": tags.pop("addr:street", None),
        }
        item["extras"] = {k: v for (k, v) in tags.items() if v}
        item = {k: v for (k, v) in item.items() if v}
        return GeojsonPointItem(**item)

    def parse_access(self, p):
        if p.get("oeffentlicher_grund") == "öffentlicher Grund":
            return {"access": "yes"}  # public grounds
        return {}

    def parse_address(self, p):
        housenumber = p.get("hausnummer")
        if street := p.get("strasse"):
            return {
                "addr:street": street,
                "addr:housenumber": housenumber,
                "addr:postcode": p.get("plz"),
                "nohousenumber": "yes" if not housenumber else None,
            }
        if addr := p.get("adresse"):
            return {"addr:full": f"{addr}, Zürich"}
        return {}

    def parse_bicycle_parking(self, p):
        amenity = {
            "Motorrad": "motorcycle_parking",
            "Velo": "bicycle_parking",
            "Beide": "bicycle_parking;motorcycle_parking",
        }.get(p["name"])
        operator, operator_wikidata = self.operators["Tiefbauamt"]
        return {
            "amenity": amenity,
            "capacity": int(p.get("anzahl_pp", 0)) or None,
            "operator": operator,
            "operator:wikidata": operator_wikidata,
        }

    def parse_name(self, p):
        names = [p.get(n) for n in ("name", "namenzus")]
        return ", ".join([n for n in names if n])

    def parse_note(self, p):
        lines = (p.get("bemerkung") or "").split("<BR>")
        lines.extend((p.get("kommentar") or "").split("<BR>"))
        lines.extend((p.get("infrastruktur") or "").split("<BR>"))
        lines = [l.strip() for l in lines]
        return " / ".join([l for l in lines if l])

    def parse_opening_hours(self, p):
        if "ist rund um die Uhr besetzt" in (p.get("bemerkung") or ""):
            return "24/7"
        oh = OpeningHours()
        for day in "Mo Di Mi Do Fr Sa So".split():
            # The counter (Schalter) can have shorter opening hours
            # than the building (Gebäude) that contains the counter.
            # We return the hours of the counter, but they aren’t set,
            # let’s fall back to the opening hours of the building.
            for part in ("schalter", "gebaeude"):  # counter, building
                if h := p.get(f"oeffnungszeiten_{part}_{day.lower()}"):
                    if h.count(";") == 3:
                        open_am, close_am, open_pm, close_pm = h.split(";")
                        if close_am and open_pm:
                            oh.add_range(
                                DAYS_DE[day], open_am, close_am, time_format="%H.%M"
                            )
                            oh.add_range(
                                DAYS_DE[day], open_pm, close_pm, time_format="%H.%M"
                            )
                        else:
                            oh.add_range(
                                DAYS_DE[day], open_am, close_pm, time_format="%H.%M"
                            )
                        break
        return oh.as_opening_hours()

    def parse_park(self, p):
        return {"leisure": "park"}

    def parse_phone(self, p):
        phone = (p.get("tel") or "").replace(" ", "")
        if phone.startswith("0"):
            phone = "+41" + phone[1:]
        return phone

    def parse_police(self, p):
        if p["name"] == "Polizeimuseum":
            return {"amenity": "museum"}
        else:
            return {"amenity": "police"}

    def parse_recycling(self, p):
        # https://wiki.openstreetmap.org/wiki/Tag:amenity%3Drecycling
        tags = {
            "glas": "glass_bottles",
            "metall": "cans",
            "oel": "oil",
            "textilien": "textiles",
        }
        recycling = {
            osm_tag for (feed_tag, osm_tag) in tags.items() if p.get(feed_tag) == "X"
        }
        return {
            "amenity": "recycling",
            "name": None,  # feed repeats address
            "recycling": ";".join(sorted(recycling)),
        }

    def parse_toilets(self, p):
        # Unstructured text in comments, which we emit as "note";
        # too unsystematic to automatically convert to structured data.
        return {"amenity": "toilets"}
