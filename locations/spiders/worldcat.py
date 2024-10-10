from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import set_closed
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class WorldcatSpider(JSONBlobSpider):
    name = "worldcat"
    locations_key = "libraries"

    def request_page(self, next_offset):
        yield JsonRequest(
            url=f"https://search.worldcat.org/api/library?lat=0&lon=0%20%20%20%20%20%20%20%20&distance=999999&unit=K&offset={next_offset}&limit=50",
            headers={"Accept": "*/*", "Referer": "https://search.worldcat.org/libraries"},
            meta={"offset": next_offset},
        )

    def start_requests(self):
        yield from self.request_page(1)

    def parse(self, response):
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features) or []
        next_offset = response.meta["offset"] + 50
        if len(response.json()["libraries"]) == 50:
            yield from self.request_page(next_offset)

    def post_process_item(self, item, response, location):
        apply_category(Categories.LIBRARY, item)

        item["ref"] = location["registryId"]
        item["name"] = location["institutionName"]
        if "closed" in item["name"].lower():
            set_closed(item)  # On initial run, all such items' names indicated they were closed
        item["street_address"] = clean_address([location.get("street1"), location.get("street2")])

        if "emails" in location:
            item["email"] = "; ".join(location["emails"])
        if "homePageUrl" in location:
            item["website"] = location["homePageUrl"]
        self.crawler.stats.inc_value(f"atp/{self.name}/type/{location['institutionType']}")
        yield item
