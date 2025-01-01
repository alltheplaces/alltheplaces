import re

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider

CASHBUILD_COUNTRIES = {
    "3": "Botswana",
    "6": "Eswatini",
    "4": "Lesotho",
    "5": "Malawi",
    "2": "Namibia",
    "1": "South Africa",
}


class CashbuildSpider(JSONBlobSpider):
    name = "cashbuild"
    item_attributes = {"brand": "Cashbuild", "brand_wikidata": "Q116474606"}
    start_urls = [
        f"https://www.cashbuild.co.za/api/getStores.php?latitude=&longitude=&country={country}"
        for country in CASHBUILD_COUNTRIES.values()
    ]
    locations_key = "result"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["street_address"] = location["physical_address"]
        item["country"] = CASHBUILD_COUNTRIES.get(str(location["country_id"]))
        item["website"] = location["external_url"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            ", ".join(
                [
                    re.sub(r"(\d\d:\d\d):(\d\d:\d\d)", r"\1-\2", re.sub(r"</?di.*?>", "", day_hours).replace("-", ""))
                    for day_hours in location["hours"]
                ]
            )
        )
        yield item
