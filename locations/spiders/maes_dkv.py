from typing import Iterable
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, FuelCards, apply_category, apply_yes_no
from locations.geo import point_locations
from locations.items import Feature
from locations.spiders.auchan_fr import AuchanFRSpider
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES
from locations.spiders.avia_eu import AviaEUSpider
from locations.spiders.bp import BpSpider
from locations.spiders.bricomarche_pl import BricomarchePLSpider
from locations.spiders.carrefour_fr import CARREFOUR_MARKET, CARREFOUR_SUPERMARKET
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.conad_it import ConadITSpider
from locations.spiders.cora_be_lu import CoraBELUSpider
from locations.spiders.e_leclerc import ELeclercSpider
from locations.spiders.eko_gr import EkoGRSpider
from locations.spiders.elinoil_gr import ElinoilGRSpider
from locations.spiders.europam_it import EuropamITSpider
from locations.spiders.f24 import F24Spider
from locations.spiders.fieten_nl import FietenNLSpider
from locations.spiders.gabriels_be import GABRIELS, POWER
from locations.spiders.globus_baumarkt_de import GlobusBaumarktDESpider
from locations.spiders.gnp_it import GnpITSpider
from locations.spiders.government.gov_osservaprezzi_carburanti_it import GovOsservaprezziCarburantiITSpider
from locations.spiders.ingo_dk import IngoDKSpider
from locations.spiders.intermarche import IntermarcheSpider
from locations.spiders.jet_de_at import JetDEATSpider
from locations.spiders.lagerhaus_at import LagerhausATSpider
from locations.spiders.loro_it import LoroITSpider
from locations.spiders.lukoil import LUKOIL_BRAND
from locations.spiders.markant_de import MarkantDESpider
from locations.spiders.maxol_ie import MaxolIESpider
from locations.spiders.mol import BRANDS_MAPPING as MOL_BRANDS_MAPPING
from locations.spiders.moya_pl import MoyaPLSpider
from locations.spiders.ok_dk import OkDKSpider
from locations.spiders.okq8 import Okq8Spider
from locations.spiders.omv import BRANDS_AND_COUNTRIES
from locations.spiders.orlen import OrlenSpider
from locations.spiders.petrol import PetrolSpider
from locations.spiders.q8_italia import Q8ItaliaSpider
from locations.spiders.repsol import RepsolSpider
from locations.spiders.rompetrol import RompetrolSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.systeme_u import SystemeUSpider
from locations.spiders.tango import TangoSpider
from locations.spiders.teboil_ru import TeboilRUSpider
from locations.spiders.texaco_co import TEXACO_SHARED_ATTRIBUTES
from locations.spiders.total_energies import TotalEnergiesSpider
from locations.spiders.yx import PREEM, UNOX, YX


def remove_key(d, key):
    r = dict(d)
    del r[key]
    return r


class MaesDkvSpider(scrapy.Spider):
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
        "ENGIE": {"brand": "Engie", "brand_wikidata": "Q13416787"},
        "RAIFFEISEN": LagerhausATSpider.item_attributes,
        "WESTFALEN": TotalEnergiesSpider.BRANDS["westfalen"],
        "TURMOEL": {"brand": "Turmöl", "brand_wikidata": "Q1473279"},
        "BP": BpSpider.brands["bp"],
        "BP STATION": BpSpider.brands["bp"],
        "TOTAL": TotalEnergiesSpider.BRANDS["tot"],
        "TOTALENERGIES": TotalEnergiesSpider.BRANDS["tot"],
        "ACCESS": TotalEnergiesSpider.BRANDS["tot"],
        "ELF": TotalEnergiesSpider.BRANDS["tot"],
        "WALTHER": {"brand": "Walther", "brand_wikidata": "Q15808406"},
        "HOYER": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "HOYER (NUR DIESEL)": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "HOYER (NUR LKW))": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "HOYER (NUR LKW)": {"brand": "Hoyer", "brand_wikidata": "Q1606119"},
        "SLOVNAFT": TotalEnergiesSpider.BRANDS["slovnaft"],
        "INA": {"brand": MOL_BRANDS_MAPPING["INA"][0], "brand_wikidata": MOL_BRANDS_MAPPING["INA"][1]},
        "DYNEFF": TotalEnergiesSpider.BRANDS["dyn"],
        "OMV": TotalEnergiesSpider.BRANDS["omv"],
        "PETRONOR": {"brand": "Petronor", "brand_wikidata": "Q1726547"},
        "PETROL": PetrolSpider.PETROL,
        "REPSOL": RepsolSpider.item_attributes,
        "CAMPSA": RepsolSpider.item_attributes,
        "INGO": IngoDKSpider.item_attributes,
        "ROMPETROL": RompetrolSpider.item_attributes,
        "ROMPETROL PARTENER": RompetrolSpider.item_attributes,
        "ROMPETROL EXPRES": RompetrolSpider.item_attributes,
        "PARTENER ROMPETROL": RompetrolSpider.item_attributes,
        "MAKPETROL": {"brand": "Макпетрол", "brand_wikidata": "Q1886438"},
        "GALP": {"brand": "Galp", "brand_wikidata": "Q1492739"},
        "SOCAR": {"brand": "SOCAR", "brand_wikidata": "Q1622293"},
        "OIL!": {"brand": "OIL!", "brand_wikidata": "Q2007561"},
        "CEPSA": TotalEnergiesSpider.BRANDS["cepsa"],
        "Q1": {"brand": "Q1", "brand_wikidata": "Q2121146"},
        "TINQ": {"brand": "TinQ", "brand_wikidata": "Q2132028"},
        "OCTA+": {"brand": "Octa+", "brand_wikidata": "Q2179978"},
        "U": SystemeUSpider.item_attributes,
        "CARREFOUR": remove_key(CARREFOUR_SUPERMARKET, "category"),
        "CARREFOUR MARKET": remove_key(CARREFOUR_MARKET, "category"),
        "SHELL": ShellSpider.item_attributes,
        "SHELL EXPRESS": {"brand": "Shell Express", "brand_wikidata": "Q2289188"},
        "DIVERSE SHELL": ShellSpider.item_attributes,
        "MOBILITY": ShellSpider.item_attributes,
        "PM / SHELL": ShellSpider.item_attributes,
        "OKTAN": {"brand": "Oktan", "brand_wikidata": "Q2316754"},
        "AVIN": {"brand": "Avin", "brand_wikidata": "Q22979634"},
        "ESSO EXPRESS": AviaEUSpider.BRANDS_MAPPING["Esso Express"],
        "ONO": {"brand": "Tank Ono", "brand_wikidata": "Q2392813"},
        "ALLGUTH": {"brand": "Allguth", "brand_wikidata": "Q2649018"},
        "OKQ8": Okq8Spider.BRANDS["OKQ8"],
        "AEGEAN": {"brand": "Aegean", "brand_wikidata": "Q28146598"},
        "AFRIQUIA": {"brand": "Afriquia", "brand_wikidata": "Q2829178"},
        "AVIA": AVIA_SHARED_ATTRIBUTES,
        "AVIA XPRESS": AVIA_SHARED_ATTRIBUTES,
        "AVIA STATION": AVIA_SHARED_ATTRIBUTES,
        "INTERMARCHE": IntermarcheSpider.INTERMARCHE,
        "EKO": EkoGRSpider.item_attributes,
        "LUKOIL": LUKOIL_BRAND,
        "CIRCLE K": CircleKSpider.CIRCLE_K,
        "K": CircleKSpider.CIRCLE_K,
        "CIRKLE K": CircleKSpider.CIRCLE_K,
        "CLASSIC": {"brand": "CLASSIC", "brand_wikidata": "Q33127117"},
        "UNO-X": UNOX,
        "IP": TotalEnergiesSpider.BRANDS["totalerg"],
        "IP MATIC": TotalEnergiesSpider.BRANDS["totalerg"],
        "TOTALERG / IP": TotalEnergiesSpider.BRANDS["totalerg"],
        "AIRLIQUIDE": {"brand": "Air Liquide", "brand_wikidata": "Q407448"},
        "Q8": Q8ItaliaSpider.item_attributes,
        "GLOBUS": GlobusBaumarktDESpider.item_attributes,
        "STATOIL 1-2-3": {"brand": "1-2-3", "brand_wikidata": "Q4545742"},
        "YX": YX,
        "ALEXELA": {"brand": "Alexela", "brand_wikidata": "Q4721301"},
        "ARGOS": {"brand": "Argos", "brand_wikidata": "Q4750477"},
        "COSTANTIN": GovOsservaprezziCarburantiITSpider.BRANDS["Costantin"],
        "MOL": TotalEnergiesSpider.BRANDS["mol"],
        "MOLGAS": TotalEnergiesSpider.BRANDS["mol"],
        "JET": JetDEATSpider.item_attributes,
        "ARAL": BpSpider.brands["aral"],
        "AGIP": GovOsservaprezziCarburantiITSpider.BRANDS["AgipEni"],
        "ENI": GovOsservaprezziCarburantiITSpider.BRANDS["AgipEni"],
        "GIAP-ENI": GovOsservaprezziCarburantiITSpider.BRANDS["AgipEni"],
        "SPRINT": {"brand": "Sprint", "brand_wikidata": "Q57588452"},
        "ELAN": TotalEnergiesSpider.BRANDS["ela"],
        "PREEM": PREEM,
        "CEPSA MOEVE": TotalEnergiesSpider.BRANDS["cepsa"],
        "NESTE": {"brand": "Neste", "brand_wikidata": "Q616376"},
        "CORA": CoraBELUSpider.item_attributes,
        "TAMOIL": AviaEUSpider.BRANDS_MAPPING["Tamoil"],
        "TAMOIL-OILONE": AviaEUSpider.BRANDS_MAPPING["Tamoil"],
        "AUCHAN": AuchanFRSpider.item_attributes,
        "TEXACO": TEXACO_SHARED_ATTRIBUTES,
        "BAYWA": {"brand": "BayWa", "brand_wikidata": "Q812055"},
        "ESSO": TotalEnergiesSpider.BRANDS["ess"],
        "STAR": OrlenSpider.brand_mappings["Star"],
        "ORLEN": OrlenSpider.brand_mappings["ORLEN"],
        "LOTOS": OrlenSpider.brand_mappings["ORLEN"],
        "HAAN": {"brand": "Haan", "brand_wikidata": "Q92553521"},
        "DE HAAN": {"brand": "Haan", "brand_wikidata": "Q92553521"},
        "BALTIC PETROLEUM": {"brand": "Baltic Petroleum", "brand_wikidata": "Q96591447"},
        "POWER": POWER,
        "FIETEN": FietenNLSpider.item_attributes,
        "DISKONT": remove_key(BRANDS_AND_COUNTRIES["HOFER"], "countries"),
        "PITPOINT": {"brand": "PitPoint", "brand_wikidata": "Q109923423"},
        "HEM": {"brand": "HEM", "brand_wikidata": "Q109930239"},
        "EUROOIL": {"brand": "EuroOil", "brand_wikidata": "Q110219457"},
        "RUEDI RUESSEL": {"brand": "Ruedi Rüssel", "brand_wikidata": "Q111725154"},
        "GNP": GnpITSpider.item_attributes,
        "EUROPAM": EuropamITSpider.item_attributes,
        "SARNI": {"brand": "Sarni", "brand_wikidata": "Q115567801"},
        "ED": {"brand": "ED", "brand_wikidata": "Q118111469"},
        "BERKMAN": {"brand": "Berkman", "brand_wikidata": "Q121742717"},
        "F24": F24Spider.BRANDS["F24"],
        "OK": OkDKSpider.item_attributes,
        "AVANTI": remove_key(BRANDS_AND_COUNTRIES["AVANTI"], "countries"),
        "BP EXPRESS": {"brand": "BP Express", "brand_wikidata": "Q124630740"},
        "ADRIA OIL": {"brand": "Adria Oil", "brand_wikidata": "Q125366355"},
        "TANGO": TangoSpider.item_attributes,
        "FLEET - TANGO": TangoSpider.item_attributes,
        "E.LECLERC": ELeclercSpider.item_attributes,
        "LECLERC": ELeclercSpider.item_attributes,
        "VIADA": {"brand": "Viada", "brand_wikidata": "Q12663942"},
        "TANKPOOL": {"brand": "tankpool24", "brand_wikidata": "Q126895471"},
        "GABRIELS": GABRIELS,
        "BEST": {"brand": "Best", "brand_wikidata": "Q127592740"},
        "LORO": LoroITSpider.item_attributes,
        "FIREZONE": AviaEUSpider.BRANDS_MAPPING["Firezone"],
        "MAXOL": MaxolIESpider.item_attributes,
        "GULF": TotalEnergiesSpider.BRANDS["gul"],
        "MARKANT": MarkantDESpider.item_attributes,
        "VITO": {"brand": "Vito", "brand_wikidata": "Q62536473"},
        "MOYA": MoyaPLSpider.item_attributes,
        "TEBOIL": TeboilRUSpider.item_attributes,
        "SMART DIESEL": {"brand": "Smart Diesel", "brand_wikidata": "Q134679450"},
        "BLISKA": OrlenSpider.brand_mappings["BLISKA"],
        "BEYFIN": GovOsservaprezziCarburantiITSpider.BRANDS["Beyfin"],
        "BRICOMARCHE": BricomarchePLSpider.item_attributes,
        "CONAD": ConadITSpider.brands["CONAD"],
        "CONAD SELF": ConadITSpider.brands["CONAD SELF 24h"],
        "ELIN": ElinoilGRSpider.item_attributes,
        "ENERGAS": GovOsservaprezziCarburantiITSpider.BRANDS["Energas"],
        "IDS": AviaEUSpider.BRANDS_MAPPING["Ids"],
        "TANKEASY": AviaEUSpider.BRANDS_MAPPING["Tankeasy"],
        "TANKPOINT": AviaEUSpider.BRANDS_MAPPING["Tankpoint"],
        "TRUCKEASY": AviaEUSpider.BRANDS_MAPPING["Truckeasy"],
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
        "BK": {"brand": "BK"},
        "BOGONI": {"brand": "Bogoni"},
        "BONAREA": {"brand": "Bonarea"},
        "BONETT": {"brand": "Bonett"},
        "BONUS": {"brand": "Bonus"},
        "BRAND OIL": {"brand": "Brand Oil"},
        "CALPAM": {"brand": "Calpam"},
        "CERTAS": {"brand": "Certas"},
        "CLEANCAR": {"brand": "Cleancar"},
        "COIL": {"brand": "Coil"},
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
        "EMSI": {"brand": "EMSI"},
        "ENDESA": {"brand": "Endesa"},
        "ENERCOOP": {"brand": "Enercoop"},
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
        "TAOIL": {"brand": "Taoil"},
        "TAP": {"brand": "TAP"},
        "TAS": {"brand": "TAS"},
        "TEAM": {"brand": "Team"},
        "TERMINAL": {"brand": "Terminal"},
        "TIBER": {"brand": "Tiber"},
        "TIFON": {"brand": "Tifon"},
        "TOIL": {"brand": "Toil"},
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
        "DIVERS / OTHERS": None,
        "DIV_ROAD SOLUTION": None,
        "EASY FUEL": None,
        "OTHERS": None,
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

        for station in result.get("data", []):
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
        apply_yes_no(Extras.CAR_WASH, item, station.get("car_washing_facility"))
        apply_yes_no("shop", item, station.get("shop_refreshments"))

        if station.get("open_24_hours"):
            item["opening_hours"] = "24/7"

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
