from locations.storefinders.metalocator import MetaLocatorSpider


class MarieCallendersUSSpider(MetaLocatorSpider):
    name = "marie_callenders_us"
    item_attributes = {"brand_wikidata": "Q6762784", "brand": "Marie Callender's"}
    brand_id = "15171"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        item["website"] = location["link"]
        yield item
