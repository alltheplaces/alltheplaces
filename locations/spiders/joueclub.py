import re
from typing import Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Metropolitan France + French overseas departments only. The storefinder also
# lists franchise stores in BE/CH/IT/LB that don't share the JouéClub brand
# consistently (some Italian entries carry no "JouéClub" in their name at all).
ALLOWED_COUNTRIES = {"FR", "GP", "MQ", "GF", "RE", "YT"}


class JoueclubSpider(SitemapSpider, StructuredDataSpider):
    name = "joueclub"
    item_attributes = {"brand": "JouéClub", "brand_wikidata": "Q3187152"}
    sitemap_urls = ["https://www.joueclub.fr/robots.txt"]
    sitemap_follow = ["Store"]
    wanted_types = ["ToyStore"]
    # Not needed for anti-bot reasons (direct requests get identical bytes to a
    # plain browser) — but AWS CodeBuild's CI network gets a consistent 502 on
    # this site's robots.txt (reproduced 3/3, direct AND with ZYTE_API_KEY set
    # but unrouted — see PR discussion), while genuine Zyte routing succeeds
    # every time. requires_proxy forces real Zyte routing instead of the
    # ZyteApiByCountryMiddleware default (skip Zyte unless this is set).
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item["country"] not in ALLOWED_COUNTRIES:
            return

        # Monaco's JSON-LD reports addressCountry "FR" even though it isn't part
        # of France; its postcode (980xx) is a more reliable marker than the
        # locality name to exclude it.
        if (item.get("postcode") or "").startswith("980"):
            return

        # NSI doesn't resolve locationSet for French overseas departments, so set
        # this explicitly rather than relying on it (single unambiguous NSI
        # entry for this brand, so no risk of miscategorising).
        apply_category(Categories.SHOP_TOYS, item)

        # One store ("Jouéclub BESANCON") has a lowercase typo in the source data.
        item["branch"] = re.sub(r"(?i)^jouéclub\s+", "", item.pop("name")).strip()

        # The JSON-LD's flat streetAddress omits the house number, and its
        # openingHoursSpecification has no dayOfWeek (every entry is `false`) so
        # it can't be parsed into valid opening_hours. A richer per-store JS blob
        # elsewhere on the page has both properly split. If that blob is ever
        # missing, fall back to what StructuredDataSpider already got from the
        # JSON-LD rather than losing the item entirely.
        store_data_js = response.xpath("//script[contains(text(), 'storeData')]/text()").get()
        if store_data_js:
            store = chompjs.parse_js_object(store_data_js.split("window.__change['2'] = ", 1)[1])["storeData"]

            address_fields = store["address"]["fields"]
            if address_fields.get("street_number"):
                item["housenumber"] = address_fields["street_number"]
                item["street"] = address_fields["street"]
                item.pop("street_address", None)

            item["opening_hours"] = OpeningHours()
            for day in sorted(store["hours"]["openingHours"], key=lambda d: d["viewPos"]):
                weekday = DAYS_FULL[day["viewPos"]]
                am_begin, am_end, pm_begin, pm_end = day["amBegin"], day["amEnd"], day["pmBegin"], day["pmEnd"]
                if not any((am_begin, am_end, pm_begin, pm_end)):
                    item["opening_hours"].set_closed(weekday)
                elif am_begin and pm_end and not am_end and not pm_begin:
                    # Open continuously through midday, e.g. Saturdays at some stores.
                    item["opening_hours"].add_range(weekday, am_begin, pm_end)
                else:
                    item["opening_hours"].add_range(weekday, am_begin, am_end)
                    item["opening_hours"].add_range(weekday, pm_begin, pm_end)

        yield item
