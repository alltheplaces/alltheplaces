from typing import Iterable

from scrapy.http import JsonRequest, Request

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class AlbertCZSpider(JSONBlobSpider):
    name = "albert_cz"
    item_attributes = {"brand": "Albert", "brand_wikidata": "Q9144241", "extras": Categories.SHOP_SUPERMARKET.value}
    start_urls = ["https://www.albert.cz/api/v1/"]

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield JsonRequest(
                url,
                data={
                    "query": """query GetStoreSearch {
                    storeSearch(lang: "en", pageSize: 5000) {
                        stores {
                            address {
                                country {
                                    isocode
                                }
                                formattedAddress
                                line1
                                phone
                                postalCode
                                town
                            }
                            description
                            openingHours {
                                groceryOpeningList {
                                    weekDay
                                    openingTime
                                    closingTime
                                    closed
                                }
                            }
                            urlName
                            geoPoint {
                                latitude
                                longitude
                            }
                        }
                    }
                }
                """
                },
                dont_filter=True,
            )

    def extract_json(self, response):
        return response.json()["data"]["storeSearch"]["stores"]

    def post_process_item(self, item, response, location):
        item["ref"] = location["urlName"]
        item["name"] = "Albert " + location["description"]
        item["phone"] = location["address"]["phone"]
        item["website"] = "https://www.albert.cz/nase-prodejny/" + location["urlName"]
        oh = OpeningHours()
        processedDays = set()
        for hours in location["openingHours"]["groceryOpeningList"]:
            # opening hours are published for the next 14 days
            if hours["weekDay"] not in processedDays:
                if hours["closed"]:
                    oh.set_closed(hours["weekDay"])
                else:
                    oh.add_range(hours["weekDay"], hours["openingTime"], hours["closingTime"], "%d/%m/%Y %H:%M:%S")
                processedDays.add(hours["weekDay"])
        item["opening_hours"] = oh.as_opening_hours()
        yield item
