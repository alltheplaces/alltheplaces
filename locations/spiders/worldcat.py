import re
from typing import AsyncIterator

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

    async def start(self) -> AsyncIterator[JsonRequest]:
        for request in self.request_page(1):
            yield request

    def parse(self, response):
        features = self.extract_json(response)
        next_offset = response.meta["offset"] + 50
        if next_offset <= response.json()["pagination"]["totalEntries"]:
            yield from self.request_page(next_offset)
        yield from self.parse_feature_array(response, features) or []

    def post_process_item(self, item, response, location):
        apply_category(Categories.LIBRARY, item)

        if institution_type := location.get("institutionType"):
            if institution_type != "PUBLIC":
                item["extras"]["access"] = "private"
            item["extras"]["worldcat:type"] = institution_type
        self.crawler.stats.inc_value(f"atp/{self.name}/type/{institution_type}")

        item["ref"] = location["registryId"]
        item["name"] = location["institutionName"]

        if "closed" in item["name"].lower():
            set_closed(item)  # On initial run, all such items' names indicated they were closed

        item["street_address"] = clean_address([location.get("street1"), location.get("street2")])

        if emails := location.get("emails"):
            if address := re.search(r"[-\w.+]+@[-\w]+\.[-\w.]+", emails[0]):
                item["email"] = address.group(0)
        if website := location.get("homePageUrl"):
            website = re.sub(r"^(https?):/?(?!/)", r"\1://", website)
            if re.fullmatch(r"https?://[\w-]+(\.[\w-]+)+(:\d+)?(/\S*)?", website):
                item["website"] = website

        yield item
