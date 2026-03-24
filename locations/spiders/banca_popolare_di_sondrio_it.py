from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BancaPopolareDiSondrioITSpider(JSONBlobSpider):
    name = "banca_popolare_di_sondrio_it"
    item_attributes = {"brand": "Banca Popolare di Sondrio", "brand_wikidata": "Q686176"}
    start_urls = [
        "https://api.onthemap.io/server/v1/api/location?dataset=filiali&key=74658562-a773-11eb-83d7-112799b4bfb8&channel=www.popso.it",
        "https://api.onthemap.io/server/v1/api/location?dataset=atm&key=74658562-a773-11eb-83d7-112799b4bfb8&channel=www.popso.it",
    ]
    locations_key = ["data", "results", "features"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = feature["indirizzo"]
        item["addr_full"] = feature["otm_data_address"]
        item["postcode"] = feature["cap"]
        item["state"] = feature["provincia"]
        item["city"] = feature["citta"]
        item["phone"] = feature["telefono"]
        item["ref"] = feature["otm_id"]
        item["opening_hours"] = OpeningHours()
        if "filiali" in response.url:
            item["name"] = " - ".join(["Banca Popolare di Sondrio", "Branch"])
            for days in feature.keys():
                if days.title() in DAYS_IT:
                    day = sanitise_day(days, DAYS_IT)
                    for time in feature[days].split(","):
                        if time:
                            open_time, close_time = time.split("-")
                            item["opening_hours"].add_range(
                                day=day, open_time=open_time.strip(), close_time=close_time.strip()
                            )
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, "prelevamento" in feature["bancomat"])
        elif "atm" in response.url:
            apply_category(Categories.ATM, item)
        yield item
