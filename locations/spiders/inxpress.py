from scrapy.http import JsonRequest

from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider

SOCIAL_MEDIA_MAP = {
    "MapFacebook": SocialMedia.FACEBOOK,
    "MapTwitter": SocialMedia.TWITTER,
    "MapLinkedIn": SocialMedia.LINKEDIN,
}


class InxpressSpider(JSONBlobSpider):
    name = "inxpress"
    item_attributes = {
        "brand": "InXpress",
        "brand_wikidata": "Q130400315",
    }
    start_urls = ["https://za.inxpress.com/api/franchise"]
    locations_key = "Franchises"
    custom_settings = {"ROBOTSTXT_OBEY": False}  # timeout on attempting to fetch robots.txt

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", headers={"content-length": 0})

    def post_process_item(self, item, response, location):
        item["country"] = location["CultureCode"].split("-")[1]
        item["branch"] = item.pop("name")
        item["website"] = f"https://{item['country'].lower()}.inxpress.com{location['URL']}"
        if mobile := location.get("MobileNumber"):
            if phone := item["phone"]:
                item["phone"] += "; " + mobile
            else:
                item["phone"] = mobile
        for service in SOCIAL_MEDIA_MAP:
            if account := location.get(service):
                set_social_media(item, service, account)
        yield item
