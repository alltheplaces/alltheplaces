from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import FIREFOX_LATEST


class BataSpider(JSONBlobSpider):
    name = "bata"
    item_attributes = {"brand": "Bata", "brand_wikidata": "Q688082"}
    start_urls = [
        "https://www.bata.com/on/demandware.store/Sites-bata-cl-Site/es_CL/Stores-FindStores",
        "https://www.bata.com/on/demandware.store/Sites-bata-cz-sfra-Site/cs_CZ/Stores-FindStores",
        "https://www.bata.com/on/demandware.store/Sites-bata-id-Site/en_ID/Stores-FindStores",
        "https://www.bata.com/on/demandware.store/Sites-bata-in-Site/en_IN/Stores-FindStores",
        "https://www.bata.com/on/demandware.store/Sites-bata-it-sfra-Site/it_IT/Stores-FindStores",
        "https://www.bata.com/on/demandware.store/Sites-bata-my-Site/en_MY/Stores-FindStores",
        "https://www.bata.com/on/demandware.store/Sites-bata-sk-sfra-Site/sk_SK/Stores-FindStores",
        "https://www.bata.com/on/demandware.store/Sites-bata-th-Site/en_TH/Stores-FindStores",
    ]
    user_agent = FIREFOX_LATEST
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = None
        item["ref"] = item.pop("name").removeprefix("BATA ")
        item["street_address"] = feature["a1"]
        item["postcode"] = feature["pCode"]
        item["state"] = feature.get("sCode")
        item["country"] = feature["cCode"]
        item["website"] = response.urljoin("{}?storeID={}".format(response.json()["controllerURL"], feature["ID"]))
        apply_category(Categories.SHOP_SHOES, item)
        yield item
