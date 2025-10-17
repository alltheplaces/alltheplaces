from typing import Iterable

from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider


class AnzSpider(JSONBlobSpider):
    name = "anz"
    item_attributes = {"brand": "ANZ", "brand_wikidata": "Q714641"}
    locations_key = "Features"

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://data.nowwhere.com.au/v3.2/features/ANZ_GLOBAL_LOCATIONS?key=lX8QnCpUMT4pv37nCCSY11Kpo4jCt6Cm8sElH7bF&bbox=-180 -90,180 90&sortBy=distance&filter=atm=1 or branch=1",
            headers={"Referer": "https://www.anz.com.au/"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = feature["uuid"]
        item["street_address"] = item.pop("street")
        item["email"] = (
            (item.get("email") or "")
            .replace("Pacopscallcentre1@anz.com", "")
            .replace("(Samoa Help Desk) ccsamoa@anz.com", "")
            .strip(" /")
        )

        if feature["active"] != "1":
            set_closed(item)

        if feature["branch"] == "1":
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, feature["atm"] == "1")
        elif feature["atm"] == "1":
            apply_category(Categories.ATM, item)

        yield item
