from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address, merge_address_lines


class VoyageCareGBSpider(JSONBlobSpider):
    name = "voyage_care_gb"
    item_attributes = {"brand": "Voyage Care", "brand_wikidata": "Q134484515"}
    allowed_domains = ["www.voyagecare.com"]
    start_urls = ["https://www.voyagecare.com/wp-json/voyagecare/v1/services/null/null/null/null/0/0/500"]
    locations_key = "body"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["branch"] = feature["post_title"]
        item["addr_full"] = clean_address([feature["address1_composite"]])
        item["street_address"] = merge_address_lines(
            [feature.get("address1_line1"), feature.get("address1_line2"), feature.get("address1_line3")]
        )
        item["city"] = feature["address1_city"]
        item["postcode"] = feature["address1_postalcode"]
        item["state"] = feature["address1_stateorprovince"]
        item["website"] = "https://www.voyagecare.com/" + feature["route"]
        apply_category(Categories.SOCIAL_FACILITY, item)
        item["extras"]["social_facility:for"] = "disabled"
        yield item
