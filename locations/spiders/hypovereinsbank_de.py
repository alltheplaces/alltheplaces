from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider


class HypovereinsbankDESpider(UberallSpider):
    name = "hypovereinsbank_de"
    item_attributes = {"brand": "HypoVereinsbank", "brand_wikidata": "Q220189"}
    key = "QZ7auxGUWKL0MfAnUOgweafKIwrXPb"
    business_id_filter = 77215
    # Ignores:
    # 599793 - Wealth Management
    # 337143 - Unternehmenskunden (corporate clients services)
    # 337141 - Private Banking

    def parse_item(self, item, feature, **kwargs):
        item["website"] = "https://www.hypovereinsbank.de/hvb/kontaktwege/filiale#!/l/{}/{}/{}".format(
            item["city"].replace(" ", "-").lower(),
            feature["streetAndNumber"].replace(" ", "-").lower(),
            feature["identifier"],
        )
        if "geldautomat" in item["name"].lower():
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        item.pop("name", None)
        yield item
