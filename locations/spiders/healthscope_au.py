from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, HealthcareSpecialities, apply_healthcare_specialities
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HealthscopeAUSpider(JSONBlobSpider):
    name = "healthscope_au"
    item_attributes = {"operator": "Healthscope", "operator_wikidata": "Q5691366", "extras": Categories.HOSPITAL.value}
    allowed_domains = ["healthscopeassist.com.au"]
    start_urls = ["https://healthscopeassist.com.au/getBoundedSites.asp?n=90&e=180&s=-90&w=-180&u=ALL&x="]
    locations_key = "data"
    requires_proxy = "AU"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["name"] == "Independence Services":
            return  # Not a hospital.
        item["ref"] = feature["site_id"]
        item["street_address"] = item.pop("addr_full", None)
        if feature.get("ed_wait_info"):
            item["extras"]["emergency"] = "yes"
            apply_healthcare_specialities([HealthcareSpecialities.EMERGENCY], item)
        else:
            item["extras"]["emergency"] = "no"
        yield item
