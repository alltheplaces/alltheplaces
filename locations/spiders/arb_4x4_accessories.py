from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class Arb4x4AccessoriesSpider(JSONBlobSpider):
    name = "arb_4x4_accessories"
    item_attributes = {"brand": "ARB 4×4 Accessories", "name": "ARB 4×4 Accessories", "brand_wikidata": "Q126166453"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = ["data", "searchAmStoreLocations", "items"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            # url="https://edge-graph.adobe.io/api/6bec9e1a-58fc-44a6-bc1a-2d8377b1a4d2/graphql",
            # Using more stable url
            url="https://mcprod.arb.com.au/graphql",
            data={"query": """
                    query SearchAmStoreLocations {
                      searchAmStoreLocations(
                        pageSize: 1000,
                        filter: {
                          attributes: [
                            { name: "4", value: "1" }   # ARB Store
                          ]
                        }
                      ) {
                        items {
                          street_address: address
                          name
                          zip
                          today_schedule
                          lat
                          lng
                          id
                          identifier
                          distance
                          country
                          attributes {
                            attribute_code
                            attribute_id
                            entity_id
                            frontend_input
                            frontend_label
                            option_title
                            value
                          }
                        }
                      }
                    }
                    """},
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("ARB ").removeprefix("Accessories ").removeprefix("4x4 ")
        item["website"] = f'https://www.arb.com.au/arb-stores/{feature["name"]}'.lower().replace(" ", "-")
        item["opening_hours"] = self.parse_opening_hours(feature["attributes"])
        apply_category(Categories.SHOP_CAR_PARTS, item)
        yield item

    def parse_opening_hours(self, location_attributes: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for attribute in location_attributes:
            if "_schedule" in attribute["attribute_code"]:
                days = attribute["attribute_code"].split("_schedule")[0].replace("weekday", "Monday-Friday")
                opening_hours.add_ranges_from_string(f'{days} {attribute["value"]}')
        return opening_hours
