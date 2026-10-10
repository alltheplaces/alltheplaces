import html
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR
from locations.items import Feature, SocialMedia, set_social_media
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GlacesMoustacheSpider(WPStoreLocatorSpider):
    name = "glaces_moustache"
    item_attributes = {
        "brand": "Glaces Moustache",
        "brand_wikidata": "Q112202767",
    }
    # Ice cream parlour chain, mostly in France with a few shops in Belgium and Spain.
    allowed_domains = ["www.glaces-moustache.fr"]
    days = DAYS_FR

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # Store names follow the pattern "Moustache <place> • Artisan Glacier".
        branch = html.unescape(feature["store"]).split("•")[0].strip()
        item["branch"] = branch.removeprefix("Moustache ").strip()
        item["name"] = self.item_attributes["brand"]

        # Source social URLs are HTML-escaped ("&#038;") and carry tracking query strings.
        # DictParser fills item["facebook"] from "facebook_url"; keep any "?id=" page ref.
        if facebook := item.get("facebook"):
            item["facebook"] = re.sub(r"[?&]locale=[^&]*", "", html.unescape(facebook)).rstrip("?")
        if instagram := feature.get("instagram_url"):
            set_social_media(item, SocialMedia.INSTAGRAM, html.unescape(instagram).split("?", 1)[0])

        apply_category(Categories.ICE_CREAM, item)
        yield item
