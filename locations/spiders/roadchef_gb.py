import json

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class RoadchefGBSpider(StructuredDataSpider):
    name = "roadchef_gb"
    item_attributes = {"operator": "Roadchef", "operator_wikidata": "Q7339582"}
    start_urls = ["https://www.roadchef.com/motorway-services"]
    wanted_types = ["LocalBusiness"]

    def parse(self, response, **kwargs):
        template = response.xpath('//wrapper/@*[name()=":template"]').get()
        for location in json.loads(template)["value"]["items"]:
            yield response.follow(location["url"], callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rstrip("/").split("/")[-1]
        item["website"] = response.url
        item.pop("twitter", None)
        item["street_address"] = None
        item["city"] = (item.get("city") or "").strip() or None
        item["postcode"] = (item.get("postcode") or "").strip() or None
        apply_category(Categories.HIGHWAY_SERVICES, item)
        yield item
