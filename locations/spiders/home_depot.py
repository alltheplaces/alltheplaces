import json
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class HomeDepotSpider(PlaywrightSpider):
    name = "home_depot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    requires_proxy = "US"
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 10,
        "USER_AGENT": BROWSER_DEFAULT,
    }
    page_size = "40"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("US", 48):
            yield JsonRequest(
                url="https://apionline.homedepot.com/federation-gateway/graphql?opname=storeSearch",
                data={
                    "operationName": "storeSearch",
                    "variables": {
                        "lat": str(lat),
                        "lng": str(lon),
                        "pagesize": self.page_size,
                        "storeSearchInput": "",
                    },
                    "query": """query storeSearch(
                      $lat: String,
                      $lng: String,
                      $storeSearchInput: String,
                      $pagesize: String,
                    ) {
                      storeSearch(
                        lat: $lat
                        lng: $lng
                        storeSearchInput: $storeSearchInput
                        pagesize: $pagesize
                      ) {
                        stores {
                          storeId
                          name
                          address {
                            street
                            city
                            state
                            postalCode
                            country
                          }
                          coordinates {
                            lat
                            lng
                          }
                          distance
                          services {
                            loadNGo
                            propane
                            toolRental
                            penske
                            keyCutting
                            wiFi
                            applianceShowroom
                            expandedFlooringShowroom
                            largeEquipment
                            kitchenShowroom
                          }
                          storeHours {
                            monday {
                              open
                              close
                            }
                            tuesday {
                              open
                              close
                            }
                            wednesday {
                              open
                              close
                            }
                            thursday {
                              open
                              close
                            }
                            friday {
                              open
                              close
                            }
                            saturday {
                              open
                              close
                            }
                            sunday {
                              open
                              close
                            }
                          }
                          storeDetailsPageLink
                          storeType
                          proDeskPhone
                          phone
                          toolRentalPhone
                        }
                        suggestedAddresses {
                          name
                          coordinates {
                            lat
                            lng
                          }
                        }
                      }
                    }
                    """,
                },
                headers={
                    "referer": "https://www.homedepot.com/",
                    "x-current-url": "/l/store-locator",
                    "x-experience-name": "store-finder",
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if stores_data := json.loads(response.xpath("//pre/text()").get()).get("data", {}).get("storeSearch"):
            for store in stores_data.get("stores", []):
                item = DictParser.parse(store)
                if item["country"] in ["CA"]:  # Home Depot CA Spider covers desired CA locations
                    continue
                item["branch"] = item.pop("name", None)
                item["street_address"] = item.pop("street", None)
                item["opening_hours"] = self.parse_opening_hours(store["storeHours"])
                apply_category(Categories.SHOP_DOITYOURSELF, item)
                apply_yes_no(Extras.WIFI, item, store["services"]["wiFi"])
                yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, hours in rules.items():
            opening_hours.add_range(day, hours["open"], hours["close"])
        return opening_hours
