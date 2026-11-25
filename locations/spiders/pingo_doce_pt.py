from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class PingoDocePTSpider(JSONBlobSpider):
    name = "pingo_doce_pt"
    item_attributes = {"brand": "Pingo Doce", "brand_wikidata": "Q1575057"}
    start_urls = ["https://www.pingodoce.pt/wp-content/themes/pingodoce/ajax/pd-ajax.php?action=pd_stores_get_stores"]
    locations_key = ["data", "stores"]
    name_is_branch = True

    def post_process_item(self, item, response, location):
        if float(item["lat"]) == 0:
            item.pop("lat")
            item.pop("lon")
        item["phone"] = location["contact"]
        item["city"] = location["county"]
        item["state"] = location["district"]
        item["website"] = response.urljoin(location["permalink"])
        item["opening_hours"] = OpeningHours()
        for day, hours in (location["schedules"]["full"] or {}).items():
            for period in ("morning", "afternoon"):
                if hours[period + "Open"] and hours[period + "Close"]:
                    item["opening_hours"].add_range(day, hours[period + "Open"], hours[period + "Close"])
        yield item
