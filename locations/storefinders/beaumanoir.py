import json
from datetime import datetime
from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse

from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BeaumanoirSpider(JSONBlobSpider):
    """
    Shared base for Groupe Beaumanoir's Salesforce Commerce Cloud store locators, whose
    `Stores-FindStores` endpoint returns every store of a site in one request given a huge radius:
    https://<domain>/on/demandware.store/Sites-<SITE>-Site/<locale>/Stores-FindStores?lat=46.6&long=2.4&radius=20000&showMap=false

    Subclasses set `name`, `item_attributes` and `start_urls`, pick their own anti-bot handling, and
    implement `include_store(store)` to drop out-of-scope stores (other brands share the same
    locator). `post_process_feature(item, feature)` can add anything brand-specific. A subclass
    `custom_settings` must extend `BeaumanoirSpider.custom_settings`, not replace it.
    """

    name_is_branch = True
    custom_settings = {
        # robots.txt disallows /on/demandware.store/.
        "ROBOTSTXT_OBEY": False,
        "ZYTE_API_SKIP_HEADERS": ["Cookie", "User-Agent"],
    }

    def extract_json(self, response: TextResponse) -> list[dict]:
        if response.meta.get("zyte_api", {}).get("browserHtml"):
            # The browser renders the JSON body inside a <pre>.
            data = json.loads(response.xpath("//pre/text()").get(""))
        else:
            data = response.json()
        cards = Selector(text=data["storesResultsHtml"]).css(".card-body[id]")
        websites = {card.attrib["id"]: card.css(".storelocator-link::attr(href)").get() for card in cards}
        return [dict(store, website=websites[store["ID"]]) for store in data["stores"] if self.include_store(store)]

    def include_store(self, store: dict) -> bool:
        raise NotImplementedError

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        custom = feature["custom"]
        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])
        if closing_date := custom["BMNR_dateFermetureDefinitive"]:
            set_closed(item, datetime.strptime(closing_date, "%d%m%Y"))

        oh = OpeningHours()
        for day, hours in json.loads(custom["BMNR_horaires"]).items():
            day = sanitise_day(day, DAYS_FR)
            # Days without a lunch break only fill ouverture_matin and fermeture_apresmidi.
            if hours.get("fermeture_matin") or hours.get("ouverture_apresmidi"):
                oh.add_range(day, hours.get("ouverture_matin"), hours.get("fermeture_matin"), "%H%M")
                oh.add_range(day, hours.get("ouverture_apresmidi"), hours.get("fermeture_apresmidi"), "%H%M")
            else:
                oh.add_range(day, hours["ouverture_matin"], hours["fermeture_apresmidi"], "%H%M")
        item["opening_hours"] = oh

        yield from self.post_process_feature(item, feature)

    def post_process_feature(self, item: Feature, feature: dict) -> Iterable[Feature]:
        yield item
