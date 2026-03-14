from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.iga import IgaSpider
from locations.spiders.irving_oil import IrvingOilSpider
from locations.spiders.london_drugs_ca import LondonDrugsCASpider
from locations.spiders.petro_canada_ca import PetroCanadaCASpider
from locations.spiders.pharmasave_ca import PharmasaveCASpider
from locations.spiders.rabba_ca import RabbaCASpider
from locations.spiders.safeway import SafewaySpider


class RoyalBankOfCanadaCASpider(JSONBlobSpider):
    name = "royal_bank_of_canada_ca"
    item_attributes = {"brand": "RBC", "brand_wikidata": "Q735261"}
    locations_key = "locations"

    LOCATED_IN_MAPPINGS = [
        (["PETRO-CANADA", "PETRO-CAN", "PETRO CANADA", "PETRO CAN"], PetroCanadaCASpider.item_attributes),
        (["ESSO"], ExxonMobilSpider.brands["Esso"]),
        (["LONDON DRUGS"], LondonDrugsCASpider.item_attributes),
        (["RABBA"], RabbaCASpider.item_attributes),
        (["IGA"], IgaSpider.item_attributes),
        (["HARNOIS"], {"brand": "Harnois Énergies", "brand_wikidata": "Q61743558"}),
        (["CIRCLE K"], CircleKSpider.CIRCLE_K),
        (["PHARMASAVE"], PharmasaveCASpider.item_attributes),
        (["IRVING"], IrvingOilSpider.item_attributes),
        (["PROXIM PHARMACIE", "PROXM PHRMC"], {"brand": "Proxim", "brand_wikidata": "Q3408523"}),
        (["SAFEWAY"], SafewaySpider.item_attributes),
        (["EKO"], {"brand": "EKO", "brand_wikidata": "Q3045934"}),
    ]

    async def start(self):
        for city in city_locations("CA", min_population=20000):
            yield scrapy.Request(
                url=f'https://maps.rbcroyalbank.com/api/?q={city["name"]}',
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        item["lat"], item["lon"] = feature.get("location")

        if feature["branch"]:
            item.pop("name")
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, feature["atm"])
        else:
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                item.get("name", ""), self.LOCATED_IN_MAPPINGS, self
            )
            apply_category(Categories.ATM, item)

        yield item
