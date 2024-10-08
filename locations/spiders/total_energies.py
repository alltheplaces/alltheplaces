import reverse_geocoder

from locations.categories import (
    Access,
    Categories,
    Extras,
    Fuel,
    FuelCards,
    PaymentMethods,
    apply_category,
    apply_yes_no,
)
from locations.items import Feature, get_lat_lon, set_lat_lon
from locations.storefinders.woosmap import WoosmapSpider


class TotalEnergiesSpider(WoosmapSpider):
    name = "total_energies"
    key = "mapstore-prod-woos"
    origin = "https://totalenergies.com"

    BRANDS = {
        "tot": {"brand": "TotalEnergies", "brand_wikidata": "Q154037"},
        "cepsa": {"brand": "Cepsa", "brand_wikidata": "Q608819"},
        "aral": {"brand": "Aral", "brand_wikidata": "Q565734"},
        "bp": {"brand": "BP", "brand_wikidata": "Q152057"},
        #   1454 "unb" - unbranded/independend
        "totalerg": {"brand": "TotalErg", "brand_wikidata": "Q3995933"},
        "ela": {"brand": "Elan", "brand_wikidata": "Q57980752"},
        "mol": {"brand": "MOL", "brand_wikidata": "Q549181"},
        "tac": {"brand": "Total Access", "brand_wikidata": "Q154037"},
        "avi": {"brand": "Avia", "brand_wikidata": "Q300147"},
        "as24": {"brand": "AS 24", "brand_wikidata": "Q2819394"},
        "ess": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "agi": {"brand": "Agip", "brand_wikidata": "Q377915"},
        "westfalen": {"brand": "Westfalen", "brand_wikidata": "Q1411209"},
        "slovnaft": {"brand": "Slovnaft", "brand_wikidata": "Q1587563"},
        "she": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "totex": {"brand": "TotalEnergies Express", "brand_wikidata": "Q154037"},
        "omv": {"brand": "OMV", "brand_wikidata": "Q168238"},
        "dyn": {"brand": "Dyneff", "brand_wikidata": "Q16630266"},
        "gul": {"brand": "Gulf", "brand_wikidata": "Q5617505"},
        "filt": {"brand": "Filoil", "brand_wikidata": None},
        #    159 "eos"
        #    151 "freie"
        #     32 "totfa"
        #     25 "sup"
        #     20 "wei"
        #     20 "haa"
        #     18 "elf"
        #      4 "deal"
        #      3 "diver"
        #      1 "g&v"
        #      1 "fin"
        #      1 "em"
    }
    SERVICES_MAPPING = {
        # Fuels
        "excellium_93": Fuel.OCTANE_93,
        "excellium95": Fuel.OCTANE_95,
        "excellium98": Fuel.OCTANE_98,
        "excelliumdiesel": Fuel.DIESEL,
        "sp95e10": Fuel.E10,
        "sp95performance": Fuel.OCTANE_95,
        "superethanole85": Fuel.E85,
        "adblue": Fuel.ADBLUE,
        "lpg": Fuel.LPG,
        "kerosene": Fuel.KEROSENE,
        "avgas100llautomate": Fuel.AV100LL,
        "avgas100ll": Fuel.AV100LL,
        "jeta1": Fuel.AVJetA1,
        "engineoil": Fuel.ENGINE_OIL,
        "wasserstoff": Fuel.LH2,
        "sp95": Fuel.OCTANE_95,
        "sp98": Fuel.OCTANE_98,
        "dieseldetruck": Fuel.HGV_DIESEL,
        # TODO: Other fuels: gasoil super superethanole85 excellium95e10 gasoline92_eg regulargasoline
        # happyfuel sp95_lb supereffimax dieseleffimax dieselb10 adbluecar
        # Payment methods
        "amex": PaymentMethods.AMERICAN_EXPRESS,
        "mastercard": PaymentMethods.MASTER_CARD,
        "visa": PaymentMethods.VISA,
        "maestro": PaymentMethods.MAESTRO,
        "vpay": PaymentMethods.V_PAY,
        "girocard": PaymentMethods.GIROCARD,
        "appay": PaymentMethods.APPLE_PAY,
        "googlepay": PaymentMethods.GOOGLE_PAY,
        "cash": PaymentMethods.CASH,
        "credit_card": PaymentMethods.CREDIT_CARDS,
        "grcartefr": "payment:gr_total_card",
        "totalcard": FuelCards.TOTAL_CARD,
        "ffc": "payment:fleet_fuel_card",
        "eurotrafic": "payment:eurotrafic",
        "carteclubtotal": "payment:club_total_card",
        "mpesa": PaymentMethods.MPESA,
        # TODO: other cards: proficard mpayment westfalencard prepaidcard travelcard ecocash nimbacard ecash sonayacard
        # Extras
        "atm": Extras.ATM,
        "absaatm": Extras.ATM,
        "bankafrica": Extras.ATM,
        "capitecatm": Extras.ATM,
        "fdhbankatm": Extras.ATM,
        "fnbatm": Extras.ATM,
        "nationalbankatm": Extras.ATM,
        "nedbank": Extras.ATM,
        "standardbank": Extras.ATM,
        "standardchartered": Extras.ATM,
        "carwash": Extras.CAR_WASH,
        "restroom": Extras.TOILETS,
        "restroom_tn": Extras.TOILETS,
        "toilets": Extras.TOILETS,
        "showers": Extras.SHOWERS,
        "freewifi": Extras.WIFI,
        "accessibility": Extras.WHEELCHAIR,
        "truckfriendly": Access.HGV,
        "oilchange": Extras.OIL_CHANGE,
        "carglass": "service:vehicle:glass",
        "generator": Extras.BACKUP_GENERATOR,
    }
    FOOD_TAGS = [
        "burgerking",
        "debonairspizza",
        "fishaways",
        "greggs",
        "hot_dog",
        "hotsnacks",
        "kfc",
        "mcdonalds",
        "pizzahut",
        "restaurant",
        "restaurant_be",
        "restaurantfr",
        "spur",
        "steers",
    ]

    def parse_item(self, item, feature, **kwargs):
        if feature["properties"]["user_properties"]["status"] != "2":
            return
        if feature["properties"]["user_properties"]["brand"] == "partners":
            return

        # Some locations have flipped coordinates - all gas stations of certain brands (Agip) and
        # some, but not all stations of other brands (Cepsa).

        lat, lon = get_lat_lon(item)
        coords_country = reverse_geocoder.get((lat, lon), mode=1, verbose=False)["cc"]
        flipped_coords_country = reverse_geocoder.get((lon, lat), mode=1, verbose=False)["cc"]
        expected_country = item["country"]

        if expected_country == flipped_coords_country and expected_country != coords_country:
            set_lat_lon(item, lon, lat)

        # As we know the name of the shop attached we create its own POI
        if "bonjour" in feature["properties"]["tags"] or "cafebonjour" in feature["properties"]["tags"]:
            bonjour_shop_item = item.deepcopy()
            bonjour_shop_item["ref"] = item.get("ref") + "-attached-shop"
            bonjour_shop_item["name"] = "Bonjour"
            bonjour_shop_item["brand"] = "Bonjour"
            bonjour_shop_item["brand_wikidata"] = "Q110278299"
            apply_category(Categories.SHOP_CONVENIENCE, bonjour_shop_item)
            yield bonjour_shop_item

        # As we do not know the name of shop/restaurant attached, we apply to main item
        if "shop" in feature["properties"]["tags"]:
            apply_yes_no("shop", item, True)

        if feature["properties"]["user_properties"]["poiType"] == "t002":
            if "be_borne_electrique" in feature["properties"]["tags"]:
                apply_category(Categories.CHARGING_STATION, item)
            else:
                apply_category(Categories.FUEL_STATION, item)
        else:
            # Other types, possibly interesting
            return

        item["website"] = f'https://store.totalenergies.fr/en_EN/{item["ref"]}'

        self.apply_services(item, feature)

        if brand := self.BRANDS.get(feature["properties"]["user_properties"]["brand"]):
            item.update(brand)
        else:
            self.crawler.stats.inc_value(
                f'atp/{self.name}/unknown_brand/{feature["properties"]["user_properties"]["brand"]}'
            )

        item["branch"] = item.pop("name")

        yield item

    def apply_services(self, item: Feature, poi: dict) -> None:
        tags = poi.get("properties", {}).get("tags", [])
        if not tags:
            return
        for tag in tags:
            if match := self.SERVICES_MAPPING.get(tag):
                apply_yes_no(match, item, True)
            elif tag in self.FOOD_TAGS:
                apply_yes_no("food", item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_tag/{tag}")
