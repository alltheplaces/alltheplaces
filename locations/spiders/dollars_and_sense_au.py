import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class DollarsAndSenseAUSpider(Spider):
    name = "dollars_and_sense_au"
    item_attributes = {"brand": "Dollars and Sense", "brand_wikidata": "Q133520267"}
    allowed_domains = ["www.dollarsense.au"]
    start_urls = ["https://www.dollarsense.au/pages/store-locations"]

    def parse(self, response: Response) -> Iterable[Feature]:
        # Coordinates are not made available. Embedded Google Maps iframes use
        # a general search/query term similar to searching Google Maps for a
        # feature such as "Dollars and Sense BranchName".
        for store in response.xpath('//div[@class="ecom-sections"]/section[position() > 1]'):
            location_details = re.sub(r'\s*:\s*', ": ", " ".join(store.xpath('.//text()').getall())).strip().removesuffix("Phone")
            location_parts = re.split(r'(?:Located in:|Address:|Phone:)', location_details)
            properties = {
                "ref": location_parts[0].removeprefix("Dollars and Sense ").strip(),
                "branch": location_parts[0].removeprefix("Dollars and Sense ").strip(),
            }
            if "Located in:" in location_details:
                properties["addr_full"] = location_parts[2]
            else:
                properties["addr_full"] = location_parts[1]
            if "Phone:" in location_details:
                properties["phone"] = location_parts[-1]
            apply_category(Categories.SHOP_VARIETY_STORE, properties)
            yield Feature(**properties)
