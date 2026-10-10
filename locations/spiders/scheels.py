import json
import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature, SocialMedia, set_social_media
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class ScheelsSpider(CamoufoxSpider):
    name = "scheels"
    item_attributes = {"name": "SCHEELS", "brand_wikidata": "Q7431070"}
    allowed_domains = ["www.scheels.com"]
    start_urls = ["https://www.scheels.com/stores/"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//div[@id="store-locator-recomm"]'

    def parse(self, response: Response) -> Iterable[Feature]:
        # Store data isn't in a dedicated API response; it's embedded as one
        # of many React Server Component "flight" payloads that Next.js
        # streams inline via self.__next_f.push(...) calls, so every chunk
        # has to be searched for the store records rather than fetched from
        # a single known key.
        for chunk in re.findall(r"self\.__next_f\.push\((\[.*?\])\)</script>", response.text, re.S):
            try:
                payload = json.loads(chunk)[1]
                body = json.loads(re.sub(r"^[0-9a-f]+:", "", payload))
            except (IndexError, TypeError, ValueError):
                continue
            yield from self.find_stores(body, response)

    def find_stores(self, obj: Any, response: Response) -> Iterable[Feature]:
        if isinstance(obj, dict):
            if obj.get("_meta", {}).get("schema") == "https://scheels.com/store":
                if item := self.parse_store(obj, response):
                    yield item
            else:
                for value in obj.values():
                    yield from self.find_stores(value, response)
        elif isinstance(obj, list):
            for value in obj:
                yield from self.find_stores(value, response)

    def parse_store(self, store: dict, response: Response) -> Feature | None:
        general = store.get("general", {})
        name = general.get("storeName")

        if general.get("comingSoon") or general.get("storeClosed") or not name:
            return None
        if "Home and Hardware" in name:
            # SCHEELS Home & Hardware is a separate hardware/home-goods
            # concept sharing the same backend, not the SCHEELS sporting
            # goods brand this spider targets.
            return None

        address = store.get("address", {}).get("address", {})
        contact = store.get("contactDetails", {})

        item = Feature()
        item["ref"] = general.get("storeID")
        item["branch"] = name
        item["street_address"] = ", ".join(filter(None, [address.get("address1"), address.get("address2")]))
        item["city"] = (address.get("city") or "").strip()
        item["state"] = address.get("state")
        item["postcode"] = address.get("postalCode")
        item["country"] = "US"
        item["phone"] = contact.get("phone")
        item["website"] = response.url

        # The site's own "latitude"/"longitude" fields are rounded to one
        # decimal place (city-level precision); the embedded Google Maps
        # link the site itself published has the real coordinates.
        if embed_url := address.get("embedUrl"):
            item["lat"], item["lon"] = url_to_coords(embed_url)

        if facebook := contact.get("facebookURL"):
            set_social_media(item, SocialMedia.FACEBOOK, facebook)
        if instagram := contact.get("instagramURL"):
            set_social_media(item, SocialMedia.INSTAGRAM, instagram)

        apply_category(Categories.SHOP_SPORTS, item)

        return item
