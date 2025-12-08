from locations.json_blob_spider import JSONBlobSpider


class CyclebarSpider(JSONBlobSpider):
    name = "cyclebar"
    item_attributes = {
        "brand": "CycleBar",
        "brand_wikidata": "Q121459827",
    }
    start_urls = ["https://members.cyclebar.com/api/brands/cyclebar/locations?open_status=external"]
    locations_key = "locations"

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        item["website"] = location["site_url"]
        yield item
