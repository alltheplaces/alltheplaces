import re

import scrapy

from locations.categories import Categories
from locations.items import Feature


class ValoraSpider(scrapy.Spider):
    name = "valora"
    allowed_domains = ["api.valora-stores.com"]
    key = "avecHnbG6Tr"
    start_urls = [
        "https://api.valora-stores.com/_index.php?apiv=2.0.9&a=data&" + f"ns=storefinder&l=de&key={key}",
    ]

    brands = {
        # For most Valora brands, we take tags such as "shop=bakery"
        # from the OpenStreetMap Name Suggestion Index (NSI).
        "avec": ("avec", "Q103863974", {}),
        "Back-Factory": ("Back-Factory", "Q21200483", {}),
        "Backwerk": ("BackWerk", "Q798298", {}),
        "Brezelkönig": ("Brezelkönig", "Q111728604", {}),
        "Cigo": ("Cigo", "Q113290782", {}),
        "Ditsch": ("Ditsch", "Q911573", {}),
        "ServiceStoreDB": ("ServiceStore DB", "Q84482517", {}),
        "Spettacolo": ("Caffè Spettacolo", "Q111728781", {}),
        "U-Store": ("U-Store", "Q113290511", {}),
        # However, the AllThePlaces pipeline does not apply any NSI rules
        # if multiple rules match with conflicting tags. We have asked the
        # local mapping community if and how exactly the conflicting NSI rules
        # should be cleaned up for "k kiosk" and "Press & Books". Meanwhile,
        # we make a call for AllThePlaces.
        "k kiosk": ("k kiosk", "Q60381703", Categories.SHOP_NEWSAGENT.value),
        "Press & Books": ("Press & Books", "Q100407277", Categories.SHOP_BOOKS.value),
        # In real life, the stores formerly called “k presse+buch” have been
        # re-branded as “Press & Books”. But as of November 2022, the Valora
        # JSON feed still uses the old name.
        "k presse+buch": ("Press & Books", "Q100407277", Categories.SHOP_BOOKS.value),
    }

    def parse(self, response):
        feed = response.json()
        countries = self.parse_countries(feed)
        brands = self.parse_brands(feed)
        stores = feed["items"]["stores"]
        columns = stores["c"]
        for store_key, store in stores["r"].items():
            properties = self.parse_brand(store, brands, columns)
            brand = properties.get("brand")
            if not brand:
                continue
            properties.update(
                {
                    "lat": store[columns["store_lat"]],
                    "lon": store[columns["store_long"]],
                    "ref": store_key,
                }
            )
            properties.update(self.parse_branch(store, brand, columns))
            properties.update(self.parse_address(store, countries, columns))
            properties = {k: v for k, v in properties.items() if v}
            for k in ["shop"]:
                if k in properties:
                    properties.setdefault("extras", {})[k] = properties[k]
                    del properties[k]
            yield Feature(**properties)

    def parse_countries(self, feed):
        countries = {}
        c = feed["props"]["laender"]
        columns = c["c"]
        for key, val in c["r"].items():
            countries[int(key)] = val[columns["land_kuerzel"]]
        return countries

    def parse_brands(self, feed):
        brands = {}
        c = feed["props"]["formate"]
        columns = c["c"]
        for key, val in c["r"].items():
            name = val[columns["format_name"]]
            brands[int(key)] = name.split("(")[0].strip()
        return brands

    def parse_branch(self, store, brand, columns):
        branch = store[columns["store_name"]]
        branch = " ".join(branch.split())  # clean up 2+ spaces
        city = store[columns["store_ort"]]
        prefixes = (
            brand,
            brand.lower(),
            brand.lower() + ".",
            brand.upper(),
            "express",
            "24/7",
            "24/7 ServiceStore",
            "Service Store DB",
            "Spettacolino",
            "AU SPETTACOLO",
            "CAFFE SPETTACOLO",
            "k presse + buch",
            "Press + Books",
            "Press&Books",
            "am",
            "im",
            ",",
            "-",
            "|",
        )
        for prefix in prefixes:
            if prefix and branch.startswith(prefix):
                branch = branch[len(prefix) :].strip()
        if branch == city or branch == brand or not branch:
            return {}

        # If the branch name contains any of these words, we also return it
        # as `located_in` tag in addition to `branch`.
        location_words = {
            "Bahnhof",
            "Hauptbahnhof",
            "S-Bahnhof",
            "ZOB",  # German abbreviation for ‘central bus station’
            "Station",
            "Tankstelle",
            "station-service",
        }

        # "Bahnhof" -> "Bahnhof Osnabrück"
        if branch in location_words:
            branch = f"{branch} {city}"

        # "Graz, Hauptbahnhof" -> "Hauptbahnhof Graz"
        for w in location_words:
            if branch.endswith(", " + w):
                branch = w + " " + branch.rsplit(",", 1)[0]
                break

        result = {"branch": branch}
        if any(word in location_words for word in branch.split()):
            result["located_in"] = branch
        return result

    def parse_brand(self, store, brands, columns):
        brand_key = brands.get(store[columns["store_format"]])
        if brand_key and brand_key.endswith("."):
            brand_key = brand_key[:-1]
        brand, brand_wikidata, tags = self.brands.get(brand_key, (None, None, None))
        if brand:
            r = {
                "brand": brand,
                "brand_wikidata": brand_wikidata,
                "name": brand,
            }
            r.update(tags)
            return r
        else:
            return {}

    def parse_address(self, store, countries, columns):
        # Valora generally passes structured addresses in their JSON feed,
        # where street and housenumber are separate fields.
        housenumber = store[columns["store_strasse_nr"]].strip()
        street = store[columns["store_strasse"]].strip()
        city = store[columns["store_ort"]].strip()
        postcode = store[columns["store_plz"]].strip()
        country = countries[store[columns["store_land"]]].upper().strip()

        # Sometimes, however, the feed’s housenumber field is empty,
        # and the street field contains a formatted address.
        if not housenumber:
            match = re.match(r"^(.+?)\s+(\d+[a-zA-Z]?)$", street)
            if match:  # German style: "Bahnhofstrasse 12"
                street = match.group(1)
                housenumber = match.group(2)
            else:  # French style: "12, Rue de la gare"
                match = re.match(r"^(\d+[a-zA-Z]?),\s+(.+)$", street)
                if match:
                    street = match.group(2)
                    housenumber = match.group(1)
        elif "/" in housenumber and not re.match(r"^\d+/\d+$", housenumber):
            # We keep housenumbers like "647/649", but clean up junk suffixes
            # such as "123/HEA" that occasionally appear in the Valora feed.
            housenumber = housenumber.split("/")[0]

        # In the Netherlands, the Valora feed sometimes passes the
        # two-letter suffix of Dutch postcodes as prefix of the city name.
        # We clean this up. ("5038", "CP Tilburg") -> ("5038 CP", "Tilburg")
        if country == "NL":
            match = re.match(r"^([A-Z]{2})\s+(.+)$", city)
            if match:
                postcode = f"{postcode} {match.group(1)}"
                city = match.group(2)

        addr = {
            "city": city,
            "country": country,
            "housenumber": housenumber,
            "postcode": postcode,
        }

        if street.endswith(","):
            street = street[:-1]
        if street.endswith("str."):
            street = street[:-4] + ("strasse" if country == "CH" else "straße")
        if street in {
            "Bahnhof",
            "Bahnhof BLS",
            "Bahnhof Oerlikon Unterführung Ost",
            "Bahnhof SBB",
            "Bahnhof Süd",
            "Gare TRN",
            "Station",
        }:
            addr["located_in"] = street
        else:
            addr["street"] = street

        return addr
