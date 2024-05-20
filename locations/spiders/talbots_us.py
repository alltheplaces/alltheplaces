import re

from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class TalbotsUSSpider(Spider):
    name = "talbots_us"
    item_attributes = {"brand": "Talbots", "brand_wikidata": "Q7679064", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["www.talbots.com"]
    start_urls = [
        "https://www.talbots.com/on/demandware.store/Sites-talbotsus-Site/default/Stores-GetNearestStores?latitude=-37.8159&longitude=144.9669&countryCode=US&distanceUnit=mi&maxdistance=15000&filterType=PRODUCT-LINE&filterValue=ALL"
    ]

    def parse(self, response):
        for store_id, store_details in response.json()["stores"].items():
            item = DictParser.parse(store_details)
            item["ref"] = store_id
            item["street_address"] = clean_address([store_details.get("address1"), store_details.get("address2")])
            item["website"] = "https://www.talbots.com/stores/{}/{}/{}/{}.html".format(
                store_details["stateCode"].lower(),
                re.sub(r"\s+", "-", re.sub(r"[^\w ]+", "", store_details["city"].lower())).strip(),
                re.sub(r"\s+", "-", re.sub(r"[^\w ]+", "", store_details["address2"].lower())).strip(),
                store_id,
            )
            hours_text = store_details.get("storeHours", "").replace("<br>", " ")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)
            yield item
