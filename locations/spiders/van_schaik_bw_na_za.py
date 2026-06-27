import json
from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class VanSchaikBWNAZASpider(JSONBlobSpider):
    name = "van_schaik_bw_na_za"
    start_urls = ["https://app.vanschaik.com/storefront/api?shop=vanschaik.myshopify.com"]
    item_attributes = {
        "brand": "Van Schaik",
        "brand_wikidata": "Q116741158",
    }
    locations_key = ["data", "metaobjects", "nodes"]

    async def start(self) -> AsyncIterator[Request]:
        payload = {
            "query": '{ metaobjects(type:"store_location",first:100){nodes{id,fields{key,value}}}}',
            "variables": {},
        }

        for url in self.start_urls:
            yield Request(
                url=url,
                method="POST",
                body=json.dumps(payload),
                callback=self.parse,
            )

    def pre_process_data(self, feature: dict) -> None:
        flattened_fields = {field["key"]: field["value"] for field in feature.pop("fields")}
        feature.clear()
        feature.update(flattened_fields)

        feature["address"] = clean_address(
            [feature.pop("address_line_1", ""), feature.pop("address_line_2", ""), feature.pop("address_line_3", "")]
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("show_on_find_a_store", "") != "true":
            return

        item["branch"] = item.pop("name")

        if item["state"] in ["Botswana", "Namibia"]:
            item["country"] = item.pop("state")
        else:
            item["country"] = "ZA"

        if item["phone"] is not None and "/" in item["phone"]:
            phones = [phone.strip() for phone in item["phone"].split("/")]
            item["phone"] = phones[0]
            for phone in phones[1:]:
                if len(phone) <= 4:
                    item["phone"] += "; " + phones[0][: -len(phone)] + phone
                else:
                    item["phone"] += "; " + phone

        if feature.get("business_hours"):
            item["opening_hours"] = OpeningHours()
            for line in feature.get("business_hours").split("\n"):
                item["opening_hours"].add_ranges_from_string(line.replace("& Public Holidays", ""))

        yield item
