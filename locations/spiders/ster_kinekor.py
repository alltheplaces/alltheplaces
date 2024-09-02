from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class SterKinekorSpider(JSONBlobSpider):
    name = "ster_kinekor"
    item_attributes = {"brand": "Ster-Kinekor", "brand_wikidata": "Q130179"}
    start_urls = ["https://www.sterkinekor.com/middleware/api/v2/regions"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                headers={
                    "X-SESSION": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJNZW1iZXJJZCI6bnVsbCwiVXNlclNlc3Npb25JZCI6IjQ0OWM1ZDUwOTY3ODRkZTM4NGEzMmFmZDBjMmY4Yzk4In0.awI61fej89WBEbnQ5Rzga0Q3JoWEMrSlvhmawSJGkZc"
                },
            )

    def extract_json(self, response):
        return [
            cinema | {"state": region["name"]} for region in response.json()["data"] for cinema in region["cinemas"]
        ]

    def post_process_item(self, item, response, location):
        item["website"] = "https://www.sterkinekor.com/find-cinemas/" + location["slug"]
        item["street_address"] = clean_address([location.get("address_1"), location.get("address_2")])
        item["branch"] = item.pop("name")
        yield item
