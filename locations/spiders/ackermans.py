from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class AckermansSpider(JSONBlobSpider):
    name = "ackermans"
    item_attributes = {
        "brand": "Ackermans",
        "brand_wikidata": "Q4674255",
    }
    start_urls = ["https://www.ackermans.co.za/graphql?operationName=ackStoresByLocation"]

    def start_requests(self):
        graphql_query = """query ackStoresByLocation($lon: Float!, $lat: Float!, $from: Int, $size: Int, $clickAndCollectOnly: Boolean, $radius: Int, $branchTypes: [String]) {
            ackStoresByLocation(
                lon: $lon
                lat: $lat
                from: $from
                size: $size
                clickAndCollectOnly: $clickAndCollectOnly
                radius: $radius
                branchTypes: $branchTypes
            ) {
                stores {
                branchCode
                branchName
                branchNameUrlKey
                clickAndCollectEnabled
                addressLine1
                addressLine2
                suburb
                suburbUrlKey
                city
                cityUrlKey
                province
                provinceUrlKey
                locDivName
                locDivNameUrlKey
                postalCode
                countryName
                countryNameUrlKey
                countryCode
                branchTelephone
                location {
                    lat
                    lon
                    __typename
                }
                businessHours {
                    ClosingTime
                    OpeningTime
                    Weekday
                    __typename
                }
                distance
                __typename
                }
                total
                __typename
            }
            }
            """
        data = {
            "operationName": "ackStoresByLocation",
            "variables": {
                "lat": -29,
                "lon": 24,
                "from": 0,
                "size": 9999,
                "clickAndCollectOnly": False,
                "radius": 10000,
                "branchTypes": None,
            },
            "query": graphql_query,
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data)

    def extract_json(self, response):
        return response.json()["data"]["ackStoresByLocation"]["stores"]

    def pre_process_data(self, location, **kwargs):
        location["street_address"] = clean_address([location.pop("addressLine1"), location.pop("addressLine2")])

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        if item["state"] in ["Namibia", "Botswana"]:
            item.pop("state")
        if item["postcode"] in ["9000", "9999", "0000"] and location["countryCode"] in ["NA", "BW"]:
            item.pop("postcode")
        item["website"] = (
            f"https://www.ackermans.co.za/store-directory/{location['countryNameUrlKey']}/{location['provinceUrlKey']}/{location['cityUrlKey']}/{location['branchNameUrlKey']}"
        )
        if location.get("businessHours") is not None:
            item["opening_hours"] = OpeningHours()
            for day_hours in location.get("businessHours"):
                day = day_hours["Weekday"]
                if day == "Public Holiday":
                    continue
                open_time = day_hours["OpeningTime"]
                close_time = day_hours["ClosingTime"]
                if open_time == close_time == "00:00":
                    continue
                item["opening_hours"].add_range(day, open_time, close_time, "%H:%M")
        yield item
