from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CapitecBankZASpider(JSONBlobSpider):
    name = "capitec_bank_za"
    item_attributes = {"brand": "Capitec Bank", "brand_wikidata": "Q5035822"}
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 300}
    requires_proxy = "ZA"

    async def start(self) -> AsyncIterator[Request]:
        yield JsonRequest(
            url="https://admin.goreview.co.za/website/api/locations/search",
            data={
                "domain": "capitecpages.localpages.io",
                "latitude": "-30.559482",
                "longitude": "22.937506",
                "attributes": "[]",
                "radius": "1000",
                "initialLoad": "true",
                "selectedCountryFilter": "null",
                "selectedProvinceFilter": "null",
                "selectedCityFilter": "null",
            },
            headers={"x-requested-by-application": "localpages"},
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["storeCode"]
        item["website"] = feature["local_page_url"]
        for location_type in ["Capitec Bank ATM", "Capitec Bank", "Capitec Business Centre"]:
            if location_type in item["name"]:
                item["name"] = location_type
                item["branch"] = item["name"].split(location_type)[1].strip()
                break
        location_attributes = [attribute["value"] for attribute in feature.get("attributes", [])]
        if "ATM" in location_attributes:
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, "Cash Accepting ATM" in location_attributes, False)
        else:
            apply_category(Categories.BANK, item)
        yield item
