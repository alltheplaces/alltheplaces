import json
import re
from typing import Any

from scrapy.http import Response

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class LasikPlusUSSpider(JSONBlobSpider):
    name = "lasik_plus_us"
    item_attributes = {"brand": "LasikPlus", "brand_wikidata": "Q126111242"}
    start_urls = ["https://www.lasikplus.com/locations/"]

    def extract_json(self, response: Response) -> list[dict]:
        return json.loads(
            re.search(
                r"locationsData\s*=\s*(\[.+?\]);",
                response.xpath('//*[@id="meta-locations-map-js-extra"]/text()').get(),
                re.DOTALL,
            ).group(1)
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        item["ref"] = str(feature["id"])
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([feature.get("address"), feature.get("address_2")])
        item["addr_full"] = None
        item["website"] = feature.get("link")
        apply_category(Categories.CLINIC, item)
        apply_healthcare_specialities([HealthcareSpecialities.OPHTHALMOLOGY], item)
        yield item
