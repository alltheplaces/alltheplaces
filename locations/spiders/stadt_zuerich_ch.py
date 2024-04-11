import re

import scrapy

from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.materials import MATERIALS_DE


# Open Data of the City of Zürich, https://data.stadt-zuerich.ch/
class StadtZuerichCHSpider(scrapy.Spider):
    name = "stadt_zuerich_ch"
    allowed_domains = ["ogd.stadt-zuerich.ch"]

    dataset_attributes = {
        "attribution": "optional",
        "attribution:name:de": "Stadt Zürich",
        "attribution:name:en": "City of Zurich",
        "attribution:website:de": "https://www.stadt-zuerich.ch/",
        "attribution:website:en": "https://www.stadt-zuerich.ch/en.html",
        "license": "Creative Commons Zero",
        "license:website:de": "https://www.stadt-zuerich.ch/portal/de/index/ogd/rahmenbedingungen.html#nutzungsbedingungen",
        "license:wikidata": "Q6938433",
    }

    operators = {
        "ERZ Entsorgung + Recycling Zürich": (
            "Entsorgung + Recycling Zürich",
            "Q1345452",
        ),
        "EWZ": ("Elektrizitätswerk der Stadt Zürich", "Q1326645"),
        "Fachschule Viventa": ("Schul- und Sportdepartement", "Q33121519"),
        "Grün Stadt Zürich": ("Grün Stadt Zürich", "Q1551785"),
        "Schulamt": ("Schulamt der Stadt Zürich", "Q115322776"),
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
        url_pattern % ("Brunnen", "wvz_brunnen"),
        url_pattern % ("Oeffentliche_Beleuchtung_der_Stadt_Zuerich", "ewz_brennstelle_p"),
        url_pattern % ("Park", "poi_park_view"),
        url_pattern % ("Sammelstelle", "poi_sammelstelle_view"),
        url_pattern % ("Schulanlagen", "poi_kindergarten_view"),
        url_pattern % ("Schulanlagen", "poi_kinderhort_view"),
        url_pattern % ("Schulanlagen", "poi_sonderschule_view"),
        url_pattern % ("Schulanlagen", "poi_volksschule_view"),
        url_pattern % ("Sitzbankkataster_OGD", "bankstandorte_ogd"),
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
        (operator, operator_wikidata) = self.operators.get(props.get("da"), (None, None))
        tags = {
            "email": props.get("mail"),
            "name": self.parse_name(props),
            "note": self.parse_note(props),
            "opening_hours": self.parse_opening_hours(props),
            "operator": operator,
            "operator:wikidata": operator_wikidata,
            "phone": self.parse_phone(props),
            "ref": props.get("poi_id") or id,
            "website": props.get("www"),
        }
        tags.update(self.parse_access(props))
        tags.update(self.parse_address(props))

        # The type-specific parsers should come after the general ones,
        # so they can overwrite tags.
        if parser := {
            "bankstandorte_ogd": self.parse_bench,
            "ewz_brennstelle_p": self.parse_street_lamp,
            "poi_kindergarten_view": self.parse_kindergarten,
            "poi_kinderhort_view": self.parse_after_school,
            "poi_park_view": self.parse_park,
            "poi_sammelstelle_view": self.parse_recycling,
            "poi_sonderschule_view": self.parse_school,
            "poi_stadtpolizei_view": self.parse_police,
            "poi_volksschule_view": self.parse_school,
            "poi_zueriwc_rs_view": self.parse_toilets,
            "wvz_brunnen": self.parse_fountain,
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
            "phone": tags.pop("phone", None),
            "postcode": tags.pop("addr:postcode", None),
            "ref": tags.pop("ref"),
            "street": tags.pop("addr:street", None),
            "operator": tags.pop("operator", None),
            "operator_wikidata": tags.pop("operator:wikidata", None),
        }
        item["extras"] = {k: v for (k, v) in tags.items() if v}
        item = {k: v for (k, v) in item.items() if v}
        return Feature(**item)

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
            if m := re.match(r"^(.+) (\d+\s?[a-kA-K]?)$", addr):
                return {
                    "addr:street": m.group(1),
                    "addr:housenumber": m.group(2),
                    "addr:postcode": p.get("plz"),
                }
            else:
                return {"addr:full": f"{addr}, Zürich"}
        return {}

    def parse_after_school(self, p):
        name = p["name"]
        amenity = "kindergarten" if "Kindergarten" in name else "school"
        oh = OpeningHours()
        for day in ["Mo", "Tu", "We", "Th", "Fr"]:
            if "Morgen" in name:
                oh.add_range(day, open_time="07:00", close_time="08:15")
            if "Mittag" in name:
                oh.add_range(day, open_time="11:55", close_time="14:00")
            if "Nachmittag" in name:
                oh.add_range(day, open_time="14:00", close_time="15:30")
            if "Abend" in name:
                oh.add_range(day, open_time="15:30", close_time="18:00")
        return {
            "amenity": amenity,
            "after_school": "yes",
            "name": name.split("(")[0].strip().removesuffix(" MoT"),
            "opening_hours": oh.as_opening_hours(),
        }

    bench_models = {
        "mit Rückenlehne": {"backrest": "yes"},
        "mit Rückenlehne und 2 Armlehnen": {
            "armrest": "yes",
            "backrest": "yes",
        },
        "ohne Rückenlehne": {"backrest": "no"},
        "mit Rückenlehne und Armlehne links": {
            "armrest": "left",
            "backrest": "yes",
        },
        "mit Rückenlehne und Armlehne rechts": {
            "armrest": "right",
            "backrest": "yes",
        },
        "Tisch-Bank-Kombination": {"picnic_table": "yes"},
        "Tisch": {"picnic_table": "yes"},
    }

    def parse_bench(self, p):
        operator, operator_wikidata = self.operators["Grün Stadt Zürich"]
        tags = {
            "amenity": "bench",
            "operator": operator,
            "operator:wikidata": operator_wikidata,
        }
        tags.update(self.bench_models.get(p.get("sitzbankmodelle"), {}))
        return tags

    def parse_bicycle_parking(self, p):
        # For bicycle and motorcycle parkings, the data feed puts the
        # feature type into the name; the parkings have no real names.
        tags = {
            "Motorrad": {"amenity": "motorcycle_parking", "bicycle": "no"},
            "Velo": {"amenity": "bicycle_parking", "motorcycle": "no"},
            "Beide": {"amenity": "bicycle_parking", "motorcycle": "yes"},
        }.get(p["name"])
        operator, operator_wikidata = self.operators["Tiefbauamt"]
        tags.update(
            {
                "capacity": str(int(p.get("anzahl_pp", 0))) or None,
                "name": None,
                "operator": operator,
                "operator:wikidata": operator_wikidata,
            }
        )
        return tags

    def parse_fountain(self, p):
        column_material, column_material_wikidata = MATERIALS_DE.get(p.get("material_saeule"), (None, None))
        sculpture_material, sculpture_material_wikidata = MATERIALS_DE.get(p.get("material_figur"), (None, None))
        trough_material, trough_material_wikidata = MATERIALS_DE.get(p.get("material_trog"), (None, None))
        if addr := (p.get("standort") or "").strip():
            addr = addr + ", Zürich"
        return {
            "addr:full": addr,
            "amenity": "fountain",
            "artist_name": p.get("steinhauer"),
            "column:material": column_material,
            "column:material:wikidata": column_material_wikidata,
            "drinking_water": "no" if p.get("abgestellt") == "ja" else "yes",
            "ref": "wvz-%s" % p["brunnennummer"],
            "sculpture:material": sculpture_material,
            "sculpture:material:wikidata": sculpture_material_wikidata,
            "start_date": str(p.get("baujahr", "")),
            "trough:material": trough_material,
            "trough:material:wikidata": trough_material_wikidata,
        }

    def parse_kindergarten(self, p):
        return {"amenity": "kindergarten", "isced:level": "0"}

    def parse_name(self, p):
        names = [p.get(n) for n in ("name", "namenzus")]
        return ", ".join([n for n in names if n])

    def parse_note(self, p):
        lines = []
        for key in ("bemerkung", "kommentar"):
            for line in (p.get(key) or "").split("<BR>"):
                line = line.strip()
                if line and line not in {"NULL", ";NULL"}:
                    lines.append(line)
        return " / ".join(lines)

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
                            oh.add_range(DAYS_DE[day], open_am, close_am, time_format="%H.%M")
                            oh.add_range(DAYS_DE[day], open_pm, close_pm, time_format="%H.%M")
                        else:
                            oh.add_range(DAYS_DE[day], open_am, close_pm, time_format="%H.%M")
                        break
        return oh.as_opening_hours()

    def parse_park(self, p):
        tags = {"leisure": "park"}
        equipment = {
            "Beachvolleyball": {"beachvolleyball": "yes"},
            "Behinderten-WC": {"toilets:wheelchair": "yes"},
            "Besuchenden-WC": {"toilets": "yes"},
            "Brunnen": {"fountain": "yes"},
            "Café": {"cafe": "yes"},
            "Feuerstelle": {"bbq": "yes"},
            "Garderobe": {"locker": "yes"},
            "Grillstelle": {"bbq": "yes"},
            "Grosse Liegewiese": {"sunbathing": "yes"},
            "Elektrogrill": {"bbq": "electric"},
            "Hundefreie Zone": {"dog": "no"},
            "Kiosk": {"kiosk": "yes"},
            "Liegewiese": {"sunbathing": "yes"},
            "Nur Blindenhunde erlaubt": {"blind:dog": "yes", "dog": "no"},
            "PingPong": {"table_tennis": "yes"},
            "Restaurant": {"restaurant": "yes"},
            "Schachspiel": {"chess": "yes"},
            "Sitzgelegenheiten": {"bench": "yes"},
            "Sitzmöglichkeiten": {"bench": "yes"},
            "Sitzbänke": {"bench": "yes"},
            "Spielplatz": {"playground": "yes"},
            "Tischtennisplatz": {"table_tennis": "yes"},
            "Trinkbrunnen": {"drinking_water": "yes"},
            "Voliere": {"aviary": "yes"},
        }
        for e in re.split(r"[;_]|<BR>", p.get("infrastruktur") or ""):
            tags.update(equipment.get(e, {}))
        return tags

    def parse_phone(self, p):
        # The data feed sometimes contains alternate phone numbers
        # in a custom abbreviated notation: "+41 44 413 76 34/35/36".
        # This seems rather exotic, so we expand it here in the spider,
        # not in PhoneCleanUpPipeline.
        if phones := [s.strip() for s in (p.get("tel") or "").split("/")]:
            main_phone = phones[0]
            return ";".join([main_phone[0 : -len(x)] + x for x in phones])
        return None

    def parse_police(self, p):
        if p["name"] == "Polizeimuseum":
            return {"tourism": "museum", "museum": "police"}
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
        recycling = {osm_tag for (feed_tag, osm_tag) in tags.items() if p.get(feed_tag) == "X"}
        return {
            "amenity": "recycling",
            "name": None,  # feed repeats address
            "recycling": ";".join(sorted(recycling)),
        }

    def parse_school(self, p):
        # https://wiki.openstreetmap.org/wiki/Key:isced:level
        isced_level = "1"
        if "Sek" in (p.get("einheit") or ""):
            isced_level = "2"
        elif p.get("da") == "Fachschule Viventa":
            isced_level = "3"
        name_words = [word for word in p["name"].split() if word not in {"Sek", "Sekundar", "Sekundarstufe"}]
        name = " ".join(name_words).removesuffix(",")
        tags = {
            "amenity": "school",
            "isced:level": isced_level,
            "name": name,
        }
        if p.get("kategorie") == "Sonderschule":
            tags["school"] = "special_education_needs"
        return tags

    def parse_street_lamp(self, p):
        operator, operator_wikidata = self.operators["EWZ"]
        return {
            "highway": "street_lamp",
            "light:direction": str(p.get("orientierung", "")),
            "operator": operator,
            "operator:wikidata": operator_wikidata,
            "ref": p["nisnr"],
        }

    def parse_toilets(self, p):
        # Unstructured text in comments, which we emit as "note";
        # too unsystematic to automatically convert to structured data.
        return {"amenity": "toilets"}
