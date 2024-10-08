import html
import json
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class TrussellTrustGBSpider(Spider):
    name = "trussell_trust_gb"
    item_attributes = {"operator_wikidata": "Q15621299"}
    start_urls = ["https://www.trusselltrust.org/get-help/find-a-foodbank/foodbank-search/?foodbank_s=all&callback=%20"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for foodbank in json.loads(response.text[2:-2]):
            for location in foodbank["foodbank_centre"] if isinstance(foodbank.get("foodbank_centre"), list) else []:
                item = Feature()
                item["name"] = html.unescape(
                    "{} - {}".format(foodbank["foodbank_information"]["name"], location.get("foodbank_name", "")).strip(
                        " -"
                    )
                )
                item["phone"] = (
                    html.unescape(location.get("foodbank_telephone_number", ""))
                    .replace(" or ", "; ")
                    .replace("/", "; ")
                )
                item["addr_full"] = merge_address_lines(
                    Selector(text=location.get("centre_address", "")).xpath("//text()").getall()
                )
                item["postcode"] = location.get("post_code")
                item["lat"] = location["centre_geolocation"]["lat"]
                item["lon"] = location["centre_geolocation"]["lng"]
                item["website"] = foodbank["foodbank_information"]["permalink"]

                item["opening_hours"] = OpeningHours()
                for rule in location.get("opening_time", []):
                    if rule["foodbank_status"] != "open":
                        continue
                    item["opening_hours"].add_range(rule["day"], rule["opening_time"], rule["closing_time"])

                yield item
