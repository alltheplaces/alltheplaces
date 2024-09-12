from chompjs import parse_js_object

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES

SOCIAL_MEDIA_MAP = {
    "instagram": SocialMedia.INSTAGRAM,
    "facebook": SocialMedia.FACEBOOK,
    "x": SocialMedia.TWITTER,
}


class ToyotaBRSpider(JSONBlobSpider):
    name = "toyota_br"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = ["https://www.toyota.com.br/contato/localize-uma-concessionaria"]

    def extract_json(self, response):
        data_raw = response.xpath('.//script[@id="__NEXT_DATA__"]/text()').get()
        return parse_js_object(data_raw.split('"dealers":')[1])

    def pre_process_data(self, location):
        location["address"]["house_number"] = location["address"].pop("number", None)
        location["website"] = location.pop("site")

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_CAR, item)

        emails = [location.get("contactEmail"), location.get("salesEmail")]
        item["email"] = "; ".join([e for e in emails if e is not None])

        set_social_media(item, SocialMedia.WHATSAPP, location.get("whatsapp"))
        if (
            location["dealerProducts"][0].get("attributes") is not None
            and location["dealerProducts"][0]["attributes"].get("socialMedia") is not None
        ):
            social_medias = location["dealerProducts"][0]["attributes"]["socialMedia"]
            for social_media in social_medias:
                if service := SOCIAL_MEDIA_MAP.get(social_media["name"]):
                    set_social_media(item, service, social_media["value"].strip())
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_social_meda/{social_media['name']}")

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(f"Mo-Fr {location.get('showRoomWeekDaysHour')}")
        item["opening_hours"].add_ranges_from_string(f"Sa {location.get('hfShowRoomSaturdayHour')}")
        item["opening_hours"].add_ranges_from_string(f"Su {location.get('hfShowRoomSundayHour')}")

        yield item
