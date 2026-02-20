from typing import Iterable

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.ampm_us import AmpmUSSpider
from locations.spiders.bp import BpSpider
from locations.spiders.chevron_us import BRANDS as CHEVRON_BRANDS
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.citgo import CitgoSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.giant_eagle_us import GiantEagleUSSpider
from locations.spiders.marathon_petroleum_us import MarathonPetroleumUSSpider
from locations.spiders.phillips_66_conoco_76 import Phillips66Conoco76Spider
from locations.spiders.quality_dairy_us import QualityDairyUSSpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.shell import ShellSpider
from locations.spiders.sinclair_us import SinclairUSSpider
from locations.spiders.sunoco_us import SunocoUSSpider
from locations.spiders.valero import ValeroSpider
from locations.storefinders.storerocket import StoreRocketSpider


class AthenaSpider(StoreRocketSpider):
    name = "athena"
    item_attributes = {"brand": "Athena Bitcoin", "brand_wikidata": "Q135280046"}
    storerocket_id = "vZ4v6A94Qd"
    time_hours_format = 12
    iseadgg_countries_list = ["US", "SV", "CO", "AR"]
    search_radius = 200

    LOCATED_IN_MAPPINGS = [
        (["HUCKS", "HUCK'S"], {"brand": "Huck's Food & Fuel", "brand_wikidata": "Q56276328"}),
        (["SHELL"], ShellSpider.item_attributes),
        (["MARATHON"], MarathonPetroleumUSSpider.brands["MARATHON"]),
        (["ARCO"], MarathonPetroleumUSSpider.brands["ARCO"]),
        (["EXXON"], ExxonMobilSpider.brands["Exxon"]),
        (["MOBIL"], ExxonMobilSpider.brands["Mobil"]),
        (["TEXACO"], CHEVRON_BRANDS["Texaco"][0]),
        (["CHEVRON"], CHEVRON_BRANDS["Chevron"][0]),
        (["BP"], BpSpider.brands["bp"]),
        (["SUNOCO"], SunocoUSSpider.item_attributes),
        (["76"], Phillips66Conoco76Spider.BRANDS["76"]),
        (["VALERO"], ValeroSpider.item_attributes),
        (["CONOCO"], Phillips66Conoco76Spider.BRANDS["CON"]),
        (["SINCLAIR"], SinclairUSSpider.item_attributes),
        (["CITGO"], CitgoSpider.item_attributes),
        (["7 ELEVEN", "7-ELEVEN"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
        (["PHILLIPS 66"], Phillips66Conoco76Spider.BRANDS["P66"]),
        (["CIRCLE K", "CIRCLEK"], CircleKSpider.CIRCLE_K),
        (["AMOCO"], BpSpider.brands["amoco"]),
        (["AMPM", "AM/PM"], AmpmUSSpider.item_attributes),
        (["GETGO", "GET GO"], GiantEagleUSSpider.GET_GO),
        (["SPINX"], {"brand": "Spinx", "brand_wikidata": "Q121851498"}),
        (["QUALITY DAIRY"], QualityDairyUSSpider.item_attributes),
    ]

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item.pop("name", None)
        item.pop("facebook", None)
        item["extras"].pop("contact:instagram", None)

        for field in location.get("fields", {}):
            if field["name"] == "Located Inside:":
                item["located_in"], item["located_in_wikidata"] = extract_located_in(
                    field["pivot_field_value"], self.LOCATED_IN_MAPPINGS, self
                )

        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        item["extras"]["cash_in"] = "yes"
        match location.get("country"):
            case "Argentina":
                item["extras"]["currency:ARS"] = "yes"
            case "Colombia":
                item["extras"]["currency:COP"] = "yes"
            case "El Salvador":
                item["extras"]["currency:USD"] = "yes"
            case None | "":
                if location.get("timezone", "").startswith("America/") or location.get("phone").startswith("+1 "):
                    item["country"] = "US"
                    item["extras"]["currency:USD"] = "yes"
            case _:
                self.logger.warning(
                    "ATM is located in country '{}' for which the local currency is undefined by this spider. The spider should be updated to map a currency for this country.".format(
                        item.get("country")
                    )
                )

        yield item
