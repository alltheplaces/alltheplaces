from copy import deepcopy
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
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

    def extract_json(self, response: Response) -> dict | list[dict]:
        data_raw = response.xpath('.//script[@id="__NEXT_DATA__"]/text()').get()
        return parse_js_object(data_raw.split('"dealers":')[1])

    def pre_process_data(self, feature: dict) -> None:
        feature["address"]["house_number"] = feature["address"].pop("number", None)
        if website := feature.pop("site"):
            if not website.startswith("http"):
                website = "https://" + website.strip()
            feature["website"] = website

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        set_social_media(item, SocialMedia.WHATSAPP, feature.get("whatsapp"))
        if (
            feature["dealerProducts"][0].get("attributes") is not None
            and feature["dealerProducts"][0]["attributes"].get("socialMedia") is not None
        ):
            social_medias = feature["dealerProducts"][0]["attributes"]["socialMedia"]
            for social_media in social_medias:
                if service := SOCIAL_MEDIA_MAP.get(social_media["name"]):
                    set_social_media(item, service, social_media["value"].strip())
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_social_meda/{social_media['name']}")

        oh = OpeningHours()
        oh.add_ranges_from_string(f"Mo-Fr {feature.get('showRoomWeekDaysHour')}")
        oh.add_ranges_from_string(f"Sa {feature.get('hfShowRoomSaturdayHour')}")
        oh.add_ranges_from_string(f"Su {feature.get('hfShowRoomSundayHour')}")
        item["opening_hours"] = oh

        services = [service["title"] for service in feature["services"]]
        for service in services:
            self.crawler.stats.inc_value(f"atp/{self.name}/services/{service}")

        shop_item = deepcopy(item)
        apply_category(Categories.SHOP_CAR, shop_item)
        apply_yes_no(Extras.TYRE_SERVICES, shop_item, "Menu de pneus" in services)
        yield shop_item

        if "Revisões periódicas" in services or "Servicio de mantenimiento" in services:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item
