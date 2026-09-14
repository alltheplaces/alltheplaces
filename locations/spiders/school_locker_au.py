import re

import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOUR_RANGE = re.compile(r"(\d{1,2}[:.]\d{2}\s*[ap]m)\s*-\s*(\d{1,2}[:.]\d{2}\s*[ap]m)", re.IGNORECASE)
STATE_POSTCODE = re.compile(r"\b(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\b\D*(\d{4})\b", re.IGNORECASE)

# These store IDs are independent, separately branded retailers (e.g. sporting
# goods/workwear franchises) which merely stock some School Locker product
# lines. They are not School Locker's own storefronts, so are excluded.
NON_BRAND_STOCKISTS = {"INTBHS", "INTLIS", "KINNEW", "GWWLIS", "SPWULV", "OSSHFD", "DNLWAR", "EDSCO"}


class SchoolLockerAUSpider(Spider):
    name = "school_locker_au"
    item_attributes = {"brand": "School Locker", "brand_wikidata": "Q126176270"}
    start_urls = ["https://theschoollocker.com.au/stores"]

    def parse(self, response):
        blob = re.search(r"function myLookup\(val\) \{\s*var lookup = (\{.*?\n\};)", response.text, re.S).group(1)
        stores = chompjs.parse_js_object(blob)

        for ref, store in stores.items():
            if "Name" not in store or ref in NON_BRAND_STOCKISTS:
                continue

            item = Feature()
            item["ref"] = ref
            item["name"] = store["Name"]
            item["addr_full"] = merge_address_lines(
                [store.get("Address1"), store.get("Address2"), store.get("Address3")]
            )

            if m := STATE_POSTCODE.search(item["addr_full"]):
                item["state"] = m.group(1).upper()
                item["postcode"] = m.group(2)

            phone = (store.get("Phone") or "").strip()
            phone = re.sub(r"\(?\bOption\s*\d+\)?", "", phone, flags=re.IGNORECASE).strip()
            if phone and "<" not in phone and len(re.sub(r"\D", "", phone)) >= 9:
                item["phone"] = phone

            email = (store.get("Email") or "").strip() + (store.get("email1Suffix") or "").strip()
            if email and "<" not in email and not email.startswith("@"):
                item["email"] = email

            item["opening_hours"] = self.parse_hours(store)

            apply_category(Categories.SHOP_CLOTHES, item)

            gmap_src = None
            if gmap := store.get("Gmap"):
                if src := re.search(r'src="([^"]+)"', gmap):
                    gmap_src = src.group(1)

            # A large proportion of the Gmap embed links are wrapped by a Mimecast
            # email-security redirect (the CMS content looks like it was pasted from
            # an email that passed through Mimecast's link-rewriting gateway). That
            # redirector is slow and appears to rate-limit/block repeat automated
            # requests, so it isn't resolved here; those stores are left without
            # coordinates rather than yielded with unreliable ones.
            if gmap_src and "mimecast.com" not in gmap_src:
                lat, lon = url_to_coords(gmap_src)
                # A handful of embed URLs use a "directions" pb= format with repeated
                # !1d/!2d/!3d segments (different meanings in each occurrence), which
                # fools the generic parser into returning the same value for lat and
                # lon. Sanity-check against Australia's bounding box before trusting it.
                if lat and lon and lat != lon and -45 < lat < -9 and 110 < lon < 155:
                    item["lat"], item["lon"] = lat, lon

            yield item

    def parse_hours(self, store: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS:
            text = (store.get(day) or "").strip()
            if not text:
                continue
            if text.lower() == "closed":
                oh.set_closed(day)
                continue
            for open_time, close_time in HOUR_RANGE.findall(text):
                oh.add_range(
                    day,
                    open_time.replace(".", ":").replace(" ", "").lower(),
                    close_time.replace(".", ":").replace(" ", "").lower(),
                    time_format="%I:%M%p",
                )
        return oh
