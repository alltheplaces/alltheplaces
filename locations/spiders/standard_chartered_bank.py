import re

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class StandardCharteredBankSpider(scrapy.Spider):
    name = "standard_chartered_bank"
    item_attributes = {"brand": "渣打國際商業銀行", "brand_wikidata": "Q62267023"}
    start_urls = ["https://www.sc.com/en/our-locations/"]

    def parse(self, response, **kwargs):
        countries = set(re.findall(r"www.sc.com\/(\w{2})/", response.text))
        for country in countries:
            if country == "bn":
                yield scrapy.Request(
                    url=f"https://www.sc.com/{country}/data/atm-branch/all-atms-branches.json",
                    cb_kwargs={"country": country},
                )
            else:
                yield scrapy.Request(
                    url=f"https://www.sc.com/{country}/data/atm-branch/v2/all-atms-branches.json",
                    cb_kwargs={"country": country},
                    callback=self.parse_details,
                )

    def parse_details(self, response, **kwargs):
        if data := response.json()["locations"]:
            for location in data:
                if "/bn/" in response.url:
                    item = DictParser.parse(location)
                else:
                    location.update(location.pop("address"))
                    item = DictParser.parse(location)
                    item["addr_full"] = clean_address(location.get("addressLines"))
                if "branch" in location["types"]:
                    apply_category(Categories.BANK, item)
                    apply_yes_no(Extras.ATM, item, "atm" in location["types"])
                else:
                    apply_category(Categories.ATM, item)
                item["branch"] = item.get("name")
                apply_yes_no(Extras.CASH_IN, item, any(key in location["types"] for key in ["cdm", "crm"]))
                item["phone"] = None
                item["ref"] = " - ".join([str(item["ref"]), kwargs["country"]])
                item["country"] = kwargs["country"]
                yield item
