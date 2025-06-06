from typing import Iterable

from requests import Response
from scrapy.http import JsonRequest, Request, Response
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaUSSpider(JSONBlobSpider):
    name = "toyota_us"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    locations_key = "dealers"


    def start_requests(self) -> Iterable[JsonRequest | Request]:
        # API can not handle huge radius coverage, therefore 
        # I decicded to use zipcodes from:
        # Alaska(99775), Florida(33040), California(91932), Washington(98221), Kansas(66952), Maine(04619)
        for zip_code in ["99775", "33040", "91932", "98221", "66952", "04619"]:
            yield Request(
                url=f"https://api.ws.dpcmaps.toyota.com/v1/dealers?searchMode=pmaProximityLayered&radiusMiles=1000&resultsMax=5000&zipcode={zip_code}",
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        full_address = item.pop("addr_full")
        location = [item.strip() for item in full_address.split(",")]
        item["street_address"] = location[0]
        item["city"] = location[1]
        item["postcode"] = location[len(location) - 1].split(" ")[1]
        item["name"] = feature["label"]
        item["website"] = feature["details"]["uriWebsite"]
        
        departments = feature["details"]["departmentInformation"]
        apply_category(Categories.SHOP_CAR, item)
        apply_yes_no(Extras.CAR_REPAIR, item, "Service" in departments)
        apply_yes_no(Extras.CAR_PARTS, item, "Parts" in departments)

        yield item