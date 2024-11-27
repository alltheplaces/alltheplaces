from locations.hours import DAYS_IT, CLOSED_IT, OpeningHours
from locations.items import set_social_media
from locations.json_blob_spider import JSONBlobSpider

class FitActiveSpider(JSONBlobSpider):
    name = "fit_active"
    item_attributes = {"brand": "FitActive", "brand_wikidata": "Q123807531"}
    start_urls = ["https://www.fitactive.it/Club/ProvaDellaMappa"]
    skip_auto_cc_domain = True # all URLs are .it, but not all places are in Italy

    def pre_process_data(self, location):
        del location["region"]
        del location["state"]
        website_path = location["title"].removeprefix("FitActive").strip().replace(" ", "")
        location["website"] = f"https://www.fitactive.it/i-club/{website_path}.php"
        location["branch"] = location["title"]
        location["title"] = "FitActive"

    def post_process_item(self, item, response, location):
        if img_path := location.get("img"):
            item["image"] = f"https://www.fitactive.it/{img_path.lstrip('/')}"
        item["branch"] = location["branch"]
        if fb := location.get("fbLinkString"):
            set_social_media(item, "facebook", fb.strip())
        if insta := location.get("linkInsta"):
            set_social_media(item, "instagram", insta.strip())
        if start := location.get("dataApertura"):
            if start != "SOON":
                item["extras"]["start_date"] = start.strip()
        item["opening_hours"] = "24/7"
        if oph := location["orari"]:
            oh = OpeningHours()
            oh.add_ranges_from_string(oph, days=DAYS_IT, closed=CLOSED_IT)
            item["extras"]["opening_hours:office"] = oh.as_opening_hours()
        yield item

