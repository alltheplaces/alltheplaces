from urllib.parse import urljoin

from locations.json_blob_spider import JSONBlobSpider

# from locations.hours import DAYS_FULL, OpeningHours


class HTPawnbrokersGBSpider(JSONBlobSpider):
    name = "h_t_pawnbrokers"
    item_attributes = {"brand": "H&T Pawnbrokers", "brand_wikidata": "Q105672451"}
    start_urls = ["https://as-handt-store-address-service.azurewebsites.net/api/AllStoreData"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["name"] = "H&T Pawnbrokers"
        item["phone"] = location["storeTelephone1"]
        item["image"] = location["storeImage"]
        item["website"] = urljoin("https://handt.co.uk/pages/", item["branch"].replace(" ", "-"))

        # opening hours are not consistent
        # oh = OpeningHours()
        # for day in DAYS_FULL:
        #    if "-" in location.get(day.lower(), {}):
        #        open,close = location.get(day.lower(), {}).split("-")
        #        open.replace(".",":")
        #        close.replace(".",":")
        #        oh.add_range(day, open, close)
        # item["opening_hours"] = oh

        if item["lat"]:
            yield item
