from typing import Iterable
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, FuelCards, apply_category, apply_yes_no
from locations.geo import point_locations
from locations.items import Feature


class MaesDKVSpider(scrapy.Spider):
    name = "maes_dkv"
    allowed_domains = ["www.maesmobility.be"]

    # Brand to Wikidata mapping
    # Organized: brands with Wikidata (sorted by Q-code), then brands without Wikidata
    BRAND_MAPPING = {
        # ═══════════════════════════════════════════════════════════════════
        # BRANDS WITH WIKIDATA (sorted by Q-code)
        # ═══════════════════════════════════════════════════════════════════
        "BFT": {"brand": "bft", "brand_wikidata": "Q1009104"},
        "BFT / SHELL": {"brand": "bft", "brand_wikidata": "Q1009104"},
        "BFT (NUR DIESEL)": {"brand": "bft", "brand_wikidata": "Q1009104"},
        "ENGIE": {"brand": "Engie", "brand_wikidata": "Q1178147"},
        "RAIFFEISEN": {"brand": "Raiffeisen", "brand_wikidata": "Q1232873"},
        "WESTFALEN": {"brand": "Westfalen", "brand_wikidata": "Q1411209"},
        "TURMOEL": {"brand": "Turmöl", "brand_wikidata": "Q1473279"},
        "BP": {"brand": "BP", "brand_wikidata": "Q152057"},
        "BP STATION": {"brand": "BP", "brand_wikidata": "Q152057"},
        "TOTAL": {"brand": "TotalEnergies", "brand_wikidata": "Q154037"},
        "TOTALENERGIES": {"brand": "TotalEnergies", "brand_wikidata": "Q154037"},
        "ACCESS": {"brand": "TotalEnergies", "brand_wikidata": "Q154037"},
        "ELF": {"brand": "TotalEnergies", "brand_wikidata": "Q154037"},
        "WALTHER": {"brand": "Walther", "brand_wikidata": "Q15808406"},
        "HOYER": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "HOYER (NUR DIESEL)": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "HOYER (NUR LKW))": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "HOYER (NUR LKW)": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "SLOVNAFT": {"brand": "Slovnaft", "brand_wikidata": "Q1587563"},
        "INA": {"brand": "INA", "brand_wikidata": "Q1662137"},
        "DYNEFF": {"brand": "Dyneff", "brand_wikidata": "Q16630266"},
        "OMV": {"brand": "OMV", "brand_wikidata": "Q168238"},
        "PETRONOR": {"brand": "Petronor", "brand_wikidata": "Q1726547"},
        "PETROL": {"brand": "Petrol", "brand_wikidata": "Q174824"},
        "REPSOL": {"brand": "Repsol", "brand_wikidata": "Q174747"},
        "CAMPSA": {"brand": "Repsol", "brand_wikidata": "Q174747"},
        "INGO": {"brand": "Ingo", "brand_wikidata": "Q17048617"},
        "ROMPETROL": {"brand": "Rompetrol", "brand_wikidata": "Q1788862"},
        "ROMPETROL PARTENER": {"brand": "Rompetrol", "brand_wikidata": "Q1788862"},
        "ROMPETROL EXPRES": {"brand": "Rompetrol", "brand_wikidata": "Q1788862"},
        "PARTENER ROMPETROL": {"brand": "Rompetrol", "brand_wikidata": "Q1788862"},
        "MAKPETROL": {"brand": "Makpetrol", "brand_wikidata": "Q1886438"},
        "GALP": {"brand": "Galp", "brand_wikidata": "Q1492739"},
        "SOCAR": {"brand": "SOCAR", "brand_wikidata": "Q1622293"},
        "OIL!": {"brand": "OIL!", "brand_wikidata": "Q2007561"},
        "CEPSA": {"brand": "Moeve", "brand_wikidata": "Q2113006"},
        "Q1": {"brand": "Q1", "brand_wikidata": "Q2121146"},
        "TINQ": {"brand": "TinQ", "brand_wikidata": "Q2132028"},
        "OCTA+": {"brand": "Octa+", "brand_wikidata": "Q2179978"},
        "U": {"brand": "Système U", "brand_wikidata": "Q2529029"},
        "CARREFOUR": {"brand": "Carrefour", "brand_wikidata": "Q217599"},
        "CARREFOUR MARKET": {"brand": "Carrefour Market", "brand_wikidata": "Q217599"},
        "SHELL": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "SHELL EXPRESS": {"brand": "Shell Express", "brand_wikidata": "Q2289188"},
        "DIVERSE SHELL": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "MOBILITY": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "PM / SHELL": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "OKTAN": {"brand": "Oktan", "brand_wikidata": "Q2316754"},
        "AVIN": {"brand": "Avin", "brand_wikidata": "Q22979634"},
        "ESSO EXPRESS": {"brand": "Esso Express", "brand_wikidata": "Q2350336"},
        "ONO": {"brand": "Ono", "brand_wikidata": "Q2392813"},
        "ALLGUTH": {"brand": "Allguth", "brand_wikidata": "Q2649018"},
        "OKQ8": {"brand": "OKQ8", "brand_wikidata": "Q2789310"},
        "AEGEAN": {"brand": "Aegean", "brand_wikidata": "Q28146598"},
        "AFRIQUIA": {"brand": "Afriquia", "brand_wikidata": "Q2829178"},
        "AVIA": {"brand": "Avia", "brand_wikidata": "Q300147"},
        "AVIA XPRESS": {"brand": "Avia Xpress", "brand_wikidata": "Q300147"},
        "AVIA STATION": {"brand": "Avia", "brand_wikidata": "Q300147"},
        "INTERMARCHE": {"brand": "Intermarché", "brand_wikidata": "Q3153200"},
        "EKO": {"brand": "EKO", "brand_wikidata": "Q31283948"},
        "LUKOIL": {"brand": "Lukoil", "brand_wikidata": "Q329347"},
        "CIRCLE K": {"brand": "Circle K", "brand_wikidata": "Q3268010"},
        "K": {"brand": "Circle K", "brand_wikidata": "Q3268010"},
        "CIRKLE K": {"brand": "Circle K", "brand_wikidata": "Q3268010"},
        "CLASSIC": {"brand": "CLASSIC", "brand_wikidata": "Q33127117"},
        "UNO-X": {"brand": "Uno-X", "brand_wikidata": "Q3362746"},
        "IP": {"brand": "IP", "brand_wikidata": "Q3788748"},
        "IP MATIC": {"brand": "IP", "brand_wikidata": "Q3788748"},
        "TOTALERG / IP": {"brand": "IP", "brand_wikidata": "Q3788748"},
        "AIRLIQUIDE": {"brand": "Air Liquide", "brand_wikidata": "Q407448"},
        "Q8": {"brand": "Q8", "brand_wikidata": "Q4119207"},
        "GLOBUS": {"brand": "Globus", "brand_wikidata": "Q457503"},
        "STATOIL 1-2-3": {"brand": "1-2-3", "brand_wikidata": "Q4545742"},
        "YX": {"brand": "YX", "brand_wikidata": "Q4580519"},
        "ALEXELA": {"brand": "Alexela", "brand_wikidata": "Q4721301"},
        "ARGOS": {"brand": "Argos", "brand_wikidata": "Q4750477"},
        "COSTANTIN": {"brand": "Costantin", "brand_wikidata": "Q48800790"},
        "MOL": {"brand": "MOL", "brand_wikidata": "Q549181"},
        "MOLGAS": {"brand": "MOL", "brand_wikidata": "Q549181"},
        "JET": {"brand": "Jet", "brand_wikidata": "Q568940"},
        "ARAL": {"brand": "Aral", "brand_wikidata": "Q565734"},
        "AGIP": {"brand": "Agip", "brand_wikidata": "Q565594"},
        "ENI": {"brand": "Eni", "brand_wikidata": "Q565594"},
        "GIAP-ENI": {"brand": "Eni", "brand_wikidata": "Q565594"},
        "SPRINT": {"brand": "Sprint", "brand_wikidata": "Q57588452"},
        "ELAN": {"brand": "Elan", "brand_wikidata": "Q57980752"},
        "PREEM": {"brand": "Preem", "brand_wikidata": "Q598835"},
        "CEPSA MOEVE": {"brand": "Moeve", "brand_wikidata": "Q608819"},
        "NESTE": {"brand": "Neste", "brand_wikidata": "Q616376"},
        "CORA": {"brand": "Cora", "brand_wikidata": "Q686643"},
        "TAMOIL": {"brand": "Tamoil", "brand_wikidata": "Q706793"},
        "TAMOIL-OILONE": {"brand": "Tamoil", "brand_wikidata": "Q706793"},
        "AUCHAN": {"brand": "Auchan", "brand_wikidata": "Q758603"},
        "TEXACO": {"brand": "Texaco", "brand_wikidata": "Q775060"},
        "BAYWA": {"brand": "BayWa", "brand_wikidata": "Q812055"},
        "ESSO": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "STAR": {"brand": "star", "brand_wikidata": "Q89432390"},
        "ORLEN": {"brand": "Orlen", "brand_wikidata": "Q971649"},
        "LOTOS": {"brand": "Orlen", "brand_wikidata": "Q971649"},
        "HAAN": {"brand": "Haan", "brand_wikidata": "Q92553521"},
        "DE HAAN": {"brand": "Haan", "brand_wikidata": "Q92553521"},
        "BALTIC PETROLEUM": {"brand": "Baltic Petroleum", "brand_wikidata": "Q96591447"},
        "POWER": {"brand": "Power", "brand_wikidata": "Q98380874"},
        "FIETEN": {"brand": "Fieten", "brand_wikidata": "Q98837500"},
        "DISKONT": {"brand": "Hofer Diskont", "brand_wikidata": "Q107803455"},
        "PITPOINT": {"brand": "PitPoint", "brand_wikidata": "Q109923423"},
        "HEM": {"brand": "HEM", "brand_wikidata": "Q109930239"},
        "EUROOIL": {"brand": "EuroOil", "brand_wikidata": "Q110219457"},
        "RUEDI RUESSEL": {"brand": "Ruedi Rüssel", "brand_wikidata": "Q111725154"},
        "GNP": {"brand": "GNP", "brand_wikidata": "Q113950825"},
        "EUROPAM": {"brand": "Europam", "brand_wikidata": "Q115268198"},
        "SARNI": {"brand": "Sarni", "brand_wikidata": "Q115567801"},
        "ED": {"brand": "ED", "brand_wikidata": "Q118111469"},
        "BERKMAN": {"brand": "Berkman", "brand_wikidata": "Q121742717"},
        "F24": {"brand": "F24", "brand_wikidata": "Q12310853"},
        "OK": {"brand": "OK", "brand_wikidata": "Q12329785"},
        "AVANTI": {"brand": "Avanti", "brand_wikidata": "Q124350461"},
        "BP EXPRESS": {"brand": "BP Express", "brand_wikidata": "Q124630740"},
        "ADRIA OIL": {"brand": "Adria Oil", "brand_wikidata": "Q125366355"},
        "TANGO": {"brand": "Tango", "brand_wikidata": "Q125867683"},
        "FLEET - TANGO": {"brand": "Tango", "brand_wikidata": "Q125867683"},
        "E.LECLERC": {"brand": "E.Leclerc", "brand_wikidata": "Q1273376"},
        "LECLERC": {"brand": "E.Leclerc", "brand_wikidata": "Q1273376"},
        "VIADA": {"brand": "Viada", "brand_wikidata": "Q12663942"},
        "TANKPOOL": {"brand": "tankpool24", "brand_wikidata": "Q126895471"},
        "GABRIELS": {"brand": "Gabriëls", "brand_wikidata": "Q127602028"},
        "BEST": {"brand": "Best", "brand_wikidata": "Q127592740"},
        "LORO": {"brand": "Loro", "brand_wikidata": "Q131832194"},
        "FIREZONE": {"brand": "Firezone", "brand_wikidata": "Q14628080"},
        "MAXOL": {"brand": "Maxol", "brand_wikidata": "Q3302837"},
        "GULF": {"brand": "Gulf", "brand_wikidata": "Q5617505"},
        "MARKANT": {"brand": "Markant", "brand_wikidata": "Q57523365"},
        "VITO": {"brand": "Vito", "brand_wikidata": "Q62536473"},
        "MOYA": {"brand": "Moya", "brand_wikidata": "Q62297700"},
        "TEBOIL": {"brand": "Teboil", "brand_wikidata": "Q7692079"},
        "SMART DIESEL": {"brand": "Smart Diesel", "brand_wikidata": "Q134679450"},
        # ═══════════════════════════════════════════════════════════════════
        # BRANDS WITHOUT WIKIDATA (alphabetically ordered)
        # ═══════════════════════════════════════════════════════════════════
        "AGLA": {"brand": "Agla"},
        "ALA": {"brand": "Ala"},
        "ALIARA": {"brand": "Aliara"},
        "ALTERNOIL": {"brand": "Alternoil"},
        "AMIC": {"brand": "Amic"},
        "AMIGO": {"brand": "Amigo"},
        "ANDAMUR": {"brand": "Andamur"},
        "ANTARES CNG": {"brand": "Antares CNG"},
        "AP": {"brand": "AP"},
        "APARCAMIENTO": {"brand": "Aparcamiento"},
        "AQUILA": {"brand": "Aquila"},
        "AVEX": {"brand": "Avex"},
        "BAVARIA": {"brand": "Bavaria"},
        "BELL OIL": {"brand": "Bell Oil"},
        "BEMOL": {"brand": "Bemol"},
        "BENZINOL": {"brand": "Benzinol"},
        "BEYFIN": {"brand": "Beyfin"},
        "BK": {"brand": "BK"},
        "BLISKA": {"brand": "Bliska"},
        "BOGONI": {"brand": "Bogoni"},
        "BONAREA": {"brand": "Bonarea"},
        "BONETT": {"brand": "Bonett"},
        "BONUS": {"brand": "Bonus"},
        "BRAND OIL": {"brand": "Brand Oil"},
        "BRICOMARCHE": {"brand": "Bricomarche"},
        "CALPAM": {"brand": "Calpam"},
        "CERTAS": {"brand": "Certas"},
        "CLEANCAR": {"brand": "Cleancar"},
        "COIL": {"brand": "Coil"},
        "CONAD": {"brand": "Conad"},
        "CONAD SELF": {"brand": "Conad"},
        "DIESEL 24": {"brand": "Diesel 24"},
        "DIS-CAR": {"brand": "Dis-Car"},
        "DISK": {"brand": "Disk"},
        "DST": {"brand": "DST"},
        "E": {"brand": "E"},
        "E.ON": {"brand": "E.ON"},
        "EASYGAS": {"brand": "Easygas"},
        "ECODROM": {"brand": "Ecodrom"},
        "ECOSTOP": {"brand": "Ecostop"},
        "EGO": {"brand": "Ego"},
        "ELIN": {"brand": "Elin"},
        "EMSI": {"brand": "EMSI"},
        "ENDESA": {"brand": "Endesa"},
        "ENERCOOP": {"brand": "Enercoop"},
        "ENERGAS": {"brand": "Energas"},
        "ENERGYCA": {"brand": "Energyca"},
        "ENERPETROLI": {"brand": "Enerpetroli"},
        "ENOVIA": {"brand": "Enovia"},
        "ENVI": {"brand": "Envi"},
        "EUROBIT": {"brand": "Eurobit"},
        "EUROPETROL": {"brand": "Europetrol"},
        "EUROTRUCK": {"brand": "Eurotruck"},
        "F. LEITNER": {"brand": "Leitner"},
        "FELTA": {"brand": "Felta"},
        "FUELPOWER": {"brand": "FuelPower"},
        "FULLI": {"brand": "Fulli"},
        "G&V": {"brand": "G&V"},
        "G & V": {"brand": "G&V"},
        "G + V": {"brand": "G&V"},
        "GASUM": {"brand": "Gasum"},
        "GAZUP": {"brand": "Gazup"},
        "GEDS": {"brand": "Geds"},
        "GENOL": {"brand": "Genol"},
        "GIAP": {"brand": "Giap"},
        "GO": {"brand": "Go"},
        "GO ON": {"brand": "Go On"},
        "GREENLINE": {"brand": "Greenline"},
        "GREENLINE (DIESEL)": {"brand": "Greenline"},
        "H2 MOBILITY": {"brand": "H2 Mobility"},
        "HAM": {"brand": "Ham"},
        "HERM": {"brand": "Herm"},
        "HIFA OIL": {"brand": "Hifa Oil"},
        "HIFA-PETROL": {"brand": "Hifa-Petrol"},
        "HIT": {"brand": "HIT"},
        "HONSEL": {"brand": "Honsel"},
        "HPLUS": {"brand": "Hplus"},
        "IDS": {"brand": "IDS"},
        "IQ": {"brand": "IQ"},
        "JOISS": {"brand": "Joiss"},
        "KEROPETROL": {"brand": "Keropetrol"},
        "KEROTRIS": {"brand": "Kerotris"},
        "KEY FUELS": {"brand": "Key Fuels"},
        "KM-PRONA": {"brand": "KM-Prona"},
        "KOHLHAMMER": {"brand": "Kohlhammer"},
        "KRUIZ": {"brand": "Kruiz"},
        "KVISTIJA": {"brand": "Kvistija"},
        "LAGERHAUS": {"brand": "Lagerhaus"},
        "LANFER": {"brand": "Lanfer"},
        "LEITNER": {"brand": "Leitner"},
        "LIQVIS": {"brand": "Liqvis"},
        "LOTHEROL": {"brand": "Lotherol"},
        "LTG": {"brand": "LTG"},
        "LUDOIL": {"brand": "Ludoil"},
        "M. PETROL": {"brand": "M. Petrol"},
        "M1": {"brand": "M1"},
        "M3": {"brand": "M3"},
        "MAES": {"brand": "Maes"},
        "MILDA": {"brand": "Milda"},
        "MINI PRIX": {"brand": "MINI PRIX"},
        "MR.WASH": {"brand": "Mr.Wash"},
        "MTB": {"brand": "MTB"},
        "MUNDORF": {"brand": "Mundorf"},
        "NETTO": {"brand": "Netto"},
        "NIKEY": {"brand": "Nikey"},
        "NOBILE": {"brand": "Nobile"},
        "NORDOEL": {"brand": "Nordöl"},
        "OCHMAN": {"brand": "Ochman"},
        "OCTANO": {"brand": "Octano"},
        "OILONE": {"brand": "Oilone"},
        "ORANGEGAS": {"brand": "Orangegas"},
        "OSCAR DRIVE": {"brand": "Oscar Drive"},
        "PAPOIL": {"brand": "Papoil"},
        "PEGAS": {"brand": "Pegas"},
        "PETROMIRALLES": {"brand": "Petromiralles"},
        "PETRONIEVES": {"brand": "Petronieves"},
        "PETREM": {"brand": "Petrem"},
        "PETROL GAMMA": {"brand": "Petrol Gamma"},
        "PETROL OFISI": {"brand": "Petrol Ofisi"},
        "PIEPRZYK": {"brand": "Pieprzyk"},
        "PINOIL": {"brand": "Pinoil"},
        "PINK": {"brand": "Pink"},
        "POLLET": {"brand": "Pollet"},
        "RAN": {"brand": "Ran"},
        "RATIO": {"brand": "Ratio"},
        "RETITALIA": {"brand": "Retitalia"},
        "ROADY": {"brand": "Roady"},
        "ROBIN OIL": {"brand": "Robin Oil"},
        "ROTH": {"brand": "Roth"},
        "RUMPOLD": {"brand": "Rumpold"},
        "SAKKO": {"brand": "Sakko"},
        "SARA1ENERGY": {"brand": "Sara1Energy"},
        "SCORE": {"brand": "Score"},
        "SERVIFIOUL": {"brand": "Servifioul"},
        "SIA": {"brand": "SIA"},
        "SMAF": {"brand": "SMAF"},
        "SMART PLUS": {"brand": "Smart Plus"},
        "SMP": {"brand": "SMP"},
        "SNG": {"brand": "SNG"},
        "SOCOGAS": {"brand": "Socogas"},
        "SOMMESE": {"brand": "Sommese"},
        "STAROIL": {"brand": "Staroil"},
        "STATOIL": {"brand": "Statoil"},
        "TANK PLUS": {"brand": "Tank Plus"},
        "TANKEASY": {"brand": "Tankeasy"},
        "TANKPOINT": {"brand": "Tankpoint"},
        "TAOIL": {"brand": "Taoil"},
        "TAP": {"brand": "TAP"},
        "TAS": {"brand": "TAS"},
        "TEAM": {"brand": "Team"},
        "TERMINAL": {"brand": "Terminal"},
        "TIBER": {"brand": "Tiber"},
        "TIFON": {"brand": "Tifon"},
        "TOIL": {"brand": "Toil"},
        "TRUCKEASY": {"brand": "Truckeasy"},
        "TURMOELQUICK": {"brand": "Turmöl Quick"},
        "TURMOEL QUICK": {"brand": "Turmöl Quick"},
        "UK FUELS": {"brand": "UK Fuels"},
        "V-GAS": {"brand": "V-Gas"},
        "VALCARCE": {"brand": "Valcarce"},
        "VEGA": {"brand": "Vega"},
        "VOEGTLIN-MEYER": {"brand": "Voegtlin-Meyer"},
        "WATIS": {"brand": "Watis"},
        "WELCOME BREAK": {"brand": "Welcome Break"},
        "WINGS": {"brand": "Wings"},
        "WISSOL": {"brand": "Wissol"},
        # Generic/unbranded (empty brand - skip branding)
        "DIVERSE / OTHERS": None,
        "DIVERSE/OTHERS": None,
        "DIV_ROAD SOLUTION": None,
        "SUPERMARKT": None,
        "#NV": None,
        "OIL": None,
        "RO": None,  # Country code, not a brand
        "PETROL COMPANY": None,  # Too generic
    }

    async def start(self):
        # Use EU centroids without country filter to get global coverage
        for lat, lon in point_locations("eu_centroids_40km_radius_country.csv"):
            # Calculate bounds from centroid
            # Using 0.4 degrees (~44km) to ensure good coverage with overlap
            lat_delta = 0.4
            lon_delta = 0.4

            params = {
                "bounds[ne][lat]": lat + lat_delta,
                "bounds[ne][lng]": lon + lon_delta,
                "bounds[sw][lat]": lat - lat_delta,
                "bounds[sw][lng]": lon - lon_delta,
            }

            url = f"https://www.maesmobility.be/api/dkv-stations?{urlencode(params)}"

            yield scrapy.Request(
                url=url,
                method="GET",
                headers={
                    "Accept": "*/*",
                },
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        result = response.json()

        # DKV API returns {"success": true, "data": [...], "meta": {...}}
        if not result.get("success"):
            return

        stations = result.get("data", [])

        for station in stations:
            item = Feature()

            self.populate_basic_fields(item, station)
            self.apply_brand_info(item, station.get("petrol_label", ""))
            apply_category(Categories.FUEL_STATION, item)
            self.apply_facilities(item, station)

            # All stations in DKV network accept DKV cards
            apply_yes_no(FuelCards.DKV, item, True)

            yield item

    def populate_basic_fields(self, item: Feature, station: dict):
        item["ref"] = str(station["id"])
        item["lat"] = station.get("latitude")
        item["lon"] = station.get("longitude")
        item["street"] = station.get("street")
        item["city"] = station.get("city")

        # Don't add postal code if value is "#NV" (not available)
        postcode = station.get("postal_code")
        if postcode and postcode != "#NV":
            item["postcode"] = postcode

        item["country"] = self.normalize_country(station.get("country"))
        item["name"] = station.get("name", "").strip()

    def apply_brand_info(self, item: Feature, title: str):
        """Extract and apply brand information from station title."""
        if not title:
            return

        brand_info = self.extract_brand(title)
        if brand_info:
            # Skip if brand name is empty (generic/unbranded stations)
            if brand_info.get("brand"):
                item.update(brand_info)
        else:
            # Log unmapped brand for analysis
            self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_brand/{title}")

    def apply_facilities(self, item: Feature, station: dict):
        # DKV API uses car_washing_facility and shop_refreshments
        if station.get("car_washing_facility"):
            apply_yes_no(Extras.CAR_WASH, item, True)
        if station.get("shop_refreshments"):
            apply_yes_no("shop", item, True)

    def extract_brand(self, title: str) -> dict | None:
        """Extract brand information from station title using direct key lookup."""
        if not title:
            return None

        title_upper = title.upper().strip()
        return self.BRAND_MAPPING.get(title_upper)

    def normalize_country(self, country: str | None) -> str | None:
        if not country:
            return None

        country_upper = country.upper()
        # Handle various spellings for common countries
        country_map = {
            "BELGI": "BE",
            "NEDERLAND": "NL",
            "LUXEMBURG": "LU",
            "GERMANY": "DE",
            "DEUTSCHLAND": "DE",
            "FRANCE": "FR",
            "SPAIN": "ES",
            "ESPANA": "ES",
            "ESPAÑA": "ES",
            "ITALY": "IT",
            "ITALIA": "IT",
            "POLAND": "PL",
            "POLSKA": "PL",
            "AUSTRIA": "AT",
            "SCHWEIZ": "CH",
            "SWITZERLAND": "CH",
        }

        for key, code in country_map.items():
            if key in country_upper:
                return code

        return None
