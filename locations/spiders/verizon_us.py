from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VerizonUSSpider(JSONBlobSpider):
    name = "verizon_us"
    item_attributes = {"brand": "Verizon", "brand_wikidata": "Q919641"}
    operators = {
        "ABC Phones of North Carolina, Inc.": ("Victra", "Q118402656"),
        "BeMobile, Inc": ("BeMobile", None),
        "Cellular Sales Management Group LLC via its affili": ("Cellular Sales", "Q5058345"),
        "Credico (USA) LLC": ("Credico", None),
        "Cydcor LLC": ("Cydcor", None),
        "Gee Papa Enterprises, Inc.": ("Team Wireless", None),
        "LCM Enterprises Inc.": ("Smartmart", None),
        "Mobile Generation, LLC": ("Mobile Generation", None),
        "R Wireless Inc": ("R Wireless", None),
        "Russell Cellular, Inc.": ("Russell Cellular", "Q125523800"),
        "The Cellular Connection, LLC": ("The Cellular Connection", "Q121336519"),
        "UNITED TELECOM USA, INC. DBA YOUR WIRELESS": ("Your Wireless", None),
        "Verizon Wireless": ("Verizon", "Q919641"),
        "Wireless Plus, Inc.": ("Wireless Plus", None),
        "Wireless Zone, LLC": ("Wireless Zone", "Q122517436"),
    }
    locations_key = ["body", "data", "stores"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("US", 458):
            yield JsonRequest(
                url="https://www.verizon.com/digital/nsa/nos/gw/retail/searchresultsdata",
                data={
                    "latitude": lat,
                    "longitude": lon,
                    "range": 10000,
                    "noOfStores": 2500,
                    "excludeIndirect": False,
                    "retrieveBy": "GEO",
                },
            )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["storeNumber"]
        item["branch"] = item.pop("name", None)
        if website := item.get("website"):
            item["website"] = (
                f'https://www.verizon.com/nextgendigital/nos/storelocator/detail/{website.removeprefix("/stores/")}'
            )

        if business_name := feature.get("businessName"):
            if operator_info := self.operators.get(business_name):
                item["operator"], item["operator_wikidata"] = operator_info
                if item["operator"] in ["Victra", "The Cellular Connection"]:  # Covered by Victra & Tcc US Spiders
                    return
            else:
                self.logger.warning(f"Unknown operator for business name: {business_name}")

        try:
            item["opening_hours"] = self.parse_opening_hours(feature)
        except Exception as e:
            self.logger.error(f"Error parsing opening hours: {e}")
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item

    def parse_opening_hours(self, feature: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAYS_3_LETTERS:
            if hours := feature.get(f"hours{day}"):
                if "Closed" in hours:
                    opening_hours.set_closed(day)
                    continue
                opening_hours.add_range(day, *hours.strip().replace("M ", "M-").split("-"), "%I:%M %p")
        return opening_hours
