import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class InduslandBankINSpider(scrapy.Spider):
    name = "indusland_bank_in"
    item_attributes = {"brand": "IndusInd Bank", "brand_wikidata": "Q2040323"}
    start_urls = ["https://www.indusind.com/bin/branch/getAllLocation?id1=atm&id2=branches&id3=registered_offices"]

    def parse(self, response, **kwargs):
        for store in response.json():
            if "sNos" in store:
                store.update({"postcode": store.get("pincode")})
                item = DictParser.parse(store)
                if store.get("identifiers") == "ATM":
                    apply_category(Categories.ATM, item)
                else:
                    apply_category(Categories.BANK, item)
                item["ref"] = "_".join(
                    [
                        store.get("identifiers"),
                        store.get("sNos"),
                    ]
                )
                yield item
