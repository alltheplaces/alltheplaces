import chompjs

from locations.categories import Categories, apply_category, apply_yes_no, Extras
from locations.json_blob_spider import JSONBlobSpider
from locations.hours import DAYS_FULL, OpeningHours


class QuickFRSpider(JSONBlobSpider):
    name = "quick_fr"
    item_attributes = {"brand": "Quick", "brand_wikidata": "Q286494"}
    allowed_domains = ["www.quick.fr"]
    start_urls = ["https://www.quick.fr/restaurants"]

    def extract_json(self, response):
        data = chompjs.parse_js_object(
            response.xpath('//script[@id="__NEXT_DATA__"]//text()').get()
        )["props"]["pageProps"]["dehydratedState"]["queries"]

        for d in data:
            if "restaurants" in d["queryKey"]:
                return d["state"]["data"]

    def pre_process_data(self, feature: dict):
        feature.update(feature["attributes"])

    def post_process_item(self, item, response, location):
        item["country"] = "FR"
        item["branch"] = item.pop("name","")
        item["website"] = "https://www.quick.fr/restaurants/" + location["slug"]

        item["opening_hours"] = OpeningHours()
        for d in DAYS_FULL:
            hours = item.get("dining"+d,None)
            if hours is not None:
                item["opening_hours"].add_ranges_from_string(d +" " + hours)

        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.WIFI,item, True if location.get("wifi","") == "Oui" else False)
        apply_yes_no(Extras.BABY_CHANGING_TABLE,item, True if location.get("changingTable","") == "Oui" else False)
        apply_yes_no(Extras.AIR_CONDITIONING,item, True if location.get("airConditioning","") == "Oui" else False)
        
        apply_yes_no(Extras.OUTDOOR_SEATING,item, True if location.get("terrace","") == "Oui" else False, apply_positive_only=False)
        apply_yes_no(Extras.DRIVE_THROUGH,item, True if location.get("drive","") == "Oui" else False, apply_positive_only=False)
        apply_yes_no(Extras.TAKEAWAY,item, True if location.get("takeaway","") == "Oui" else False, apply_positive_only=False)
        apply_yes_no(Extras.WHEELCHAIR,item, True if location.get("pmr","") == "Oui" else False, apply_positive_only=False)

        yield item
