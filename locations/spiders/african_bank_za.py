import re

import scrapy

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class AfricanBankZASpider(scrapy.Spider):
    name = "african_bank_za"
    item_attributes = {"brand": "African Bank", "brand_wikidata": "Q4689703", "extras": Categories.BANK.value}
    allowed_domains = ["api.locationbank.net"]
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=6ef8638f-af8c-409d-ad24-cf3422269370"
    ]

    def parse(self, response):
        data = response.json()

        # This is slightly unecessary now, but saving it for later in case of other websites using locationbank.net to see how the detailViewUrl looks
        detail_view_key = re.search("\{(.+)\}", data["detailViewUrl"]).group(1)
        if detail_view_key == "locationid":
            detail_view_key = "id"

        for i in data["locations"]:
            i["phone"] = i.pop("primaryPhone")
            if i["additionalPhone1"]:
                i["phone"] += "; " + i.pop("additionalPhone1")
            i["province"] = i.pop("administrativeArea")
            i["website"] = re.sub(r"\{.+\}", i[detail_view_key], data["detailViewUrl"])
            i["street_address"] = clean_address([i.pop("addressLine1"), i.get("addressLine2")])
            item = DictParser.parse(i)
            item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
            item["opening_hours"] = OpeningHours()
            for day in i["regularHours"]:
                if day["isOpen"]:
                    item["opening_hours"].add_range(day["openDay"], day["openTime"], day["closeTime"])
                else:
                    item["opening_hours"].set_closed(day["openDay"])

            apply_yes_no(Extras.ATM, item, "ATM" in i["slAttributes"])
            # Unhandled: "Business Services", "Specialized Services"

            yield item
