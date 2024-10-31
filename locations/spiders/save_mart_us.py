from urllib.parse import quote

from scrapy.http import JsonRequest

from locations.categories import PaymentMethods, apply_yes_no
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider

brands = {
    "a3b11717-f4ca-4196-b670-e5142c205dee": {"brand": "Lucky", "brand_wikidata": "Q6698032"},
    "b0fbc8a0-c305-4adc-97c0-80d7548ea2f9": {"brand": "Save Mart", "brand_wikidata": "Q7428009"},
    "ed5181c4-4323-4bac-9e4a-e5ca92c3de68": {"brand": "FoodMaxx", "brand_wikidata": "Q61894844"},
}


class SaveMartUSSpider(JSONBlobSpider):
    name = "save_mart_us"
    locations_key = ["data", "stores", "all"]

    def start_requests(self):
        for brand in ["fm", "lu", "sm"]:
            yield JsonRequest(
                f"https://{brand}.swiftlyapi.net/graphql",
                data={
                    "query": """
                        {
                            stores {
                                all {
                                    address1
                                    chainId
                                    city
                                    country
                                    latitude
                                    longitude
                                    number
                                    payments
                                    postalCode
                                    primaryDetails {
                                        hours {
                                            day
                                            hours {
                                                close
                                                open
                                            }
                                        }
                                        name
                                        contactNumbers {
                                            imageId
                                            value
                                        }
                                    }
                                    state
                                    storeId
                                }
                            }
                        }
                    """
                },
            )

    def post_process_item(self, item, response, location):
        item.update(brands[location["chainId"]])

        item["ref"] = location["number"]
        item["branch"] = location["primaryDetails"]["name"]
        item["website"] = (
            f"https://luckysupermarkets.com/stores/{location['storeId']}/{quote(location['primaryDetails']['name'])}/{location['number']}/{quote(location['city'])}"
        )

        apply_yes_no(PaymentMethods.CASH, item, "CASH" in location["payments"])
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "CREDIT" in location["payments"])

        oh = OpeningHours()
        for day in location["primaryDetails"]["hours"]:
            for hours in day["hours"]:
                oh.add_range(
                    DAYS_3_LETTERS_FROM_SUNDAY[day["day"]], hours["open"], hours["close"], time_format="%H:%M:%S"
                )
        item["opening_hours"] = oh

        for contact_number in location["primaryDetails"]["contactNumbers"]:
            if contact_number["imageId"] == "main_phone_icon":
                item["phone"] = contact_number["value"]
            elif contact_number["imageId"] == "fax_phone_icon":
                item["extras"]["fax"] = contact_number["value"]

        yield item
