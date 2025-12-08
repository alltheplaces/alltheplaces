from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider

SOCIAL_MEDIA_MAP = {
    "facebook": SocialMedia.FACEBOOK,
    "instagram": SocialMedia.INSTAGRAM,
    "tripadvisor_link": SocialMedia.TRIPADVISOR,
}


class SouthernSunSpider(JSONBlobSpider):
    name = "southern_sun"
    item_attributes = {
        "brand": "Southern Sun",
        "brand_wikidata": "Q7570526",
    }
    start_urls = ["https://www.southernsun.com/json/properties.json"]

    def post_process_item(self, item, response, location):
        item["website"] = "https://www.southernsun.com/" + location["slug"]
        item["email"] = location["attributes"].get("contact_email")
        item["phone"] = location["attributes"].get("cards_reservations")
        item["image"] = location.get("image_link")
        if not item["image"].startswith("http"):
            item["image"] = "https:" + item["image"]
        for social_media in SOCIAL_MEDIA_MAP:
            if social_media in location["attributes"]:
                set_social_media(item, SOCIAL_MEDIA_MAP.get(social_media), location["attributes"][social_media])
        yield item
