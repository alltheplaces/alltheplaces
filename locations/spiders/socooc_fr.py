import json
import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class SocoocFRSpider(Spider):
    name = "socooc_fr"
    item_attributes = {"brand": "SoCoo'c", "brand_wikidata": "Q62783840"}
    api_requested = False

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.socooc.com/", callback=self.parse_home)

    def parse_home(self, response: Response, **kwargs: Any) -> Any:
        for chunk in response.xpath('//link[@rel="modulepreload"]/@href').getall():
            yield response.follow(chunk, callback=self.parse_chunk)

    def parse_chunk(self, response: Response, **kwargs: Any) -> Any:
        if self.api_requested:
            return
        if m := re.search(r'fournierWebservice:\{apiKey:"<Bearer>([^"]+)"', response.text):
            self.api_requested = True
            yield JsonRequest(
                "https://api.socooc.com/elasticsearch?networkId=195&q=AllStores",
                data={
                    "query": "_search",
                    "index": "indice-socooc-store",
                    "body": {
                        "query": {
                            "bool": {
                                "filter": [
                                    {"term": {"search_api_datasource": "entity:node"}},
                                    {"term": {"search_api_language": "fr"}},
                                ]
                            }
                        },
                        "from": 0,
                        "size": 10000,
                    },
                },
                headers={"Authorization": f"Bearer {m.group(1)}"},
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for hit in response.json()["hits"]["hits"]:
            location = hit["_source"]
            if location.get("operational_status") or location.get("field_temporary_close") == [True]:
                continue

            item = Feature()
            item["ref"] = item["website"] = "https://www.socooc.com" + location["url"][0]
            item["lat"] = location["lat"][0]
            item["lon"] = location["lon"][0]
            item["street_address"] = merge_address_lines(
                [location["field_adresse_1"][0], *location.get("field_adresse_2", [])]
            )
            item["postcode"] = location["field_code_postal"][0]
            item["phone"] = location["field_tel"][0]
            item["branch"] = re.sub(r"^so\s?coo['’]?c\s*", "", location["title"][0], flags=re.IGNORECASE)

            item["opening_hours"] = oh = OpeningHours()
            for day, hours in json.loads(location["weekly_opening_hours"][0]).items():
                if hours["isOpen"]:
                    for slot in hours["timeSlots"]:
                        oh.add_range(day, slot["start"], slot["end"])
                else:
                    oh.set_closed(day)

            apply_category(Categories.SHOP_KITCHEN, item)
            yield item
