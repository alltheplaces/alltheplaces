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
from locations.items import get_lat_lon, set_lat_lon
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

    def parse_item(self, item, feature, **kwargs):
        if feature["properties"]["user_properties"]["status"] != "2":
            return
        if feature["properties"]["user_properties"]["brand"] == "partners":
            return
        if feature["properties"]["user_properties"]["poiType"] == "t002":
            if "be_borne_electrique" in feature["properties"]["tags"]:
                apply_category(Categories.CHARGING_STATION, item)
            else:
                apply_category(Categories.FUEL_STATION, item)
        else:
            # Other types, possibly interesting
            return

        item["website"] = f'https://store.totalenergies.fr/en_EN/{item["ref"]}'

        apply_yes_no(Extras.ATM, item, "atm" in feature["properties"]["tags"])
        apply_yes_no(Extras.CAR_WASH, item, "carwash" in feature["properties"]["tags"])
        apply_yes_no(Extras.TOILETS, item, "restroom" in feature["properties"]["tags"])
        apply_yes_no(Extras.WIFI, item, "freewifi" in feature["properties"]["tags"])
        apply_yes_no(Extras.WHEELCHAIR, item, "accessibility" in feature["properties"]["tags"])
        apply_yes_no(Access.HGV, item, "truckfriendly" in feature["properties"]["tags"])
        apply_yes_no(Extras.OIL_CHANGE, item, "oilchange" in feature["properties"]["tags"])
        apply_yes_no("service:vehicle:glass", item, "carglass" in feature["properties"]["tags"])

        apply_yes_no(Fuel.ENGINE_OIL, item, "engineoil" in feature["properties"]["tags"])
        apply_yes_no(Fuel.AV100LL, item, "avgas100llautomate" in feature["properties"]["tags"])
        apply_yes_no(Fuel.AV100LL, item, "avgas100ll" in feature["properties"]["tags"])
        apply_yes_no(Fuel.AVJetA1, item, "jeta1" in feature["properties"]["tags"])
        apply_yes_no(Fuel.OCTANE_95, item, "excellium95" in feature["properties"]["tags"])
        apply_yes_no(Fuel.OCTANE_98, item, "excellium98" in feature["properties"]["tags"])
        apply_yes_no(Fuel.DIESEL, item, "excelliumdiesel" in feature["properties"]["tags"])
        apply_yes_no(Fuel.E10, item, "sp95e10" in feature["properties"]["tags"])
        apply_yes_no(Fuel.ADBLUE, item, "adblue" in feature["properties"]["tags"])
        apply_yes_no(Fuel.LPG, item, "lpg" in feature["properties"]["tags"])
        apply_yes_no(Fuel.KEROSENE, item, "kerosene" in feature["properties"]["tags"])
        # TODO: Other fuels?:
        # gasoil sp95 sp98 super superethanole85 excellium95e10 gasoline92_eg regulargasoline superethanole85
        # sp95performance happyfuel sp95_lb supereffimax dieseleffimax dieselb10 adbluecar excellium_93

        apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "amex" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "mastercard" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.VISA, item, "visa" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.MAESTRO, item, "maestro" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.V_PAY, item, "vpay" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.GIROCARD, item, "girocard" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.APPLE_PAY, item, "appay" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "googlepay" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.CASH, item, "cash" in feature["properties"]["tags"])
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "credit_card" in feature["properties"]["tags"])
        apply_yes_no("payment:gr_total_card", item, "grcartefr" in feature["properties"]["tags"])
        apply_yes_no(FuelCards.TOTAL_CARD, item, "totalcard" in feature["properties"]["tags"])
        apply_yes_no("payment:fleet_fuel_card", item, "ffc" in feature["properties"]["tags"])
        apply_yes_no("payment:eurotrafic", item, "eurotrafic" in feature["properties"]["tags"])
        apply_yes_no("payment:club_total_card", item, "carteclubtotal" in feature["properties"]["tags"])
        # TODO: other cards: proficard bonjour mpayment westfalencard prepaidcard travelcard ecocash nimbacard ecash sonayacard

        if "shop" in feature["properties"]["tags"]:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        if brand := self.BRANDS.get(feature["properties"]["user_properties"]["brand"]):
            item.update(brand)
        else:
            self.crawler.stats.inc_value(
                f'atp/total_energies/unknown_brand/{feature["properties"]["user_properties"]["brand"]}'
            )

        # Some locations have flipped coordinates - all gas stations of certain brands (Agip) and
        # some, but not all stations of other brands (Cepsa).

        lat, lon = get_lat_lon(item)
        coords_country = reverse_geocoder.get((lat, lon), mode=1, verbose=False)["cc"]
        flipped_coords_country = reverse_geocoder.get((lon, lat), mode=1, verbose=False)["cc"]
        expected_country = item["country"]

        if expected_country == flipped_coords_country and expected_country != coords_country:
            set_lat_lon(item, lon, lat)

        yield item
