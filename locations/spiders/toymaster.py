from typing import Iterable

from scrapy.http import Request, Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class ToymasterSpider(JSONBlobSpider):
    name = "toymaster"
    item_attributes = {"brand": "Toymaster", "brand_wikidata": "Q7830615"}
    start_urls = [
        "https://api.toymaster.co.uk/stores?status=Active&storefinder=&locale=en-GB&api_key=137601c9-ef9c-41e1-8f07-a4cde23f8c7c"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        if not feature["Mainshop"] and not feature["Shop"]:
            return
        if feature["Branding"] == "Garden Centre":
            return
        item["street_address"] = merge_address_lines(
            [feature.get("Address1"), feature.get("Address2"), feature.get("Address3"), feature.get("Address4")]
        )
        item["website"] = feature.get("Website")
        if item["website"]:
            if not item["website"].startswith("http"):
                item["website"] = "https://" + item["website"]

        item["facebook"] = feature["SocialFacebook"]
        item["twitter"] = feature["SocialTwitter"]
        # item["instagram"] = feature["SocialInstagram"]
        item["email"] = feature["Email"]
        item["phone"] = feature["Phone"]
        item["ref"] = feature["ANA"]
        item["name"] = feature["BranchName"]
        # Could add opening hours
        yield item
