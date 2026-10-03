import html
import re
from typing import Any, AsyncIterator
from urllib.parse import unquote

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature

# A large number of older stores use a legacy "maps.google.com.my/maps?q=..."
# link with a raw "N02.93163, E101.31520"-style decimal-degree pair (with an
# inconsistent mix of separators/whitespace) that locations.google_url's
# url_to_coords() cannot parse. It is still the site publishing a coordinate
# pin it already has (not a geocoded address), so it's extracted directly.
LEGACY_COORD_PATTERN = re.compile(r"q=\s*N?\s*(\d{1,3}\.\d+)\s*,?\s*E?\s*(\d{1,3}\.\d+)")

MY_STATE_ISO_CODES = {
    "johor": "MY-01",
    "kedah": "MY-02",
    "kelantan": "MY-03",
    "melaka": "MY-04",
    "negeri_sembilan": "MY-05",
    "pahang": "MY-06",
    "penang": "MY-07",
    "perak": "MY-08",
    "perlis": "MY-09",
    "selangor": "MY-10",
    "terengganu": "MY-11",
    "sabah": "MY-12",
    "sarawak": "MY-13",
    "kuala_lumpur": "MY-14",
    "labuan": "MY-15",
    "putrajaya": "MY-16",
}


class NinetynineSpeedmartMYSpider(Spider):
    name = "99_speedmart_my"
    item_attributes = {"brand": "99 Speedmart", "brand_wikidata": "Q62075061", "name": "99 Speedmart"}
    allowed_domains = ["99speedmart.com.my"]

    def make_request(self, page: int) -> FormRequest:
        # The store-locations page's own "Load More" button re-requests this
        # Jet Smart Filters AJAX endpoint (the same one the "wp-json/wp/v2/stores"
        # API is fronted by, but this one includes the address/maps fields the
        # bare REST API leaves empty for ~80% of records) and appends the
        # returned HTML fragment to the grid already on the page.
        # "defaults[paged]" is what actually selects the page of results;
        # "props[page]" (as sent by the browser) is only an echo of the
        # client's last-known state and is otherwise ignored server-side.
        return FormRequest(
            "https://99speedmart.com.my/wp-admin/admin-ajax.php",
            formdata={
                "action": "jet_smart_filters",
                "provider": "epro-loop-builder/storelocation",
                "query[__s_query|search]": "",
                "defaults[has_custom_pagination]": "true",
                "defaults[post_status]": "publish",
                "defaults[post_type]": "stores",
                "defaults[orderby]": "post_date",
                "defaults[order]": "desc",
                "defaults[paged]": str(page),
                "settings[widget_id]": "a09cddc",
                "settings[filtered_post_id]": "3404",
            },
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[FormRequest]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()

        for store in Selector(text=data["content"]).css("div.e-loop-item"):
            title = html.unescape(" ".join(store.css("p.elementor-heading-title::text").getall())).strip()
            if not title or "–" not in title:
                continue

            ref, _, branch = title.partition("–")
            ref = ref.strip()

            addr_full = " ".join(
                store.css("div.elementor-widget-text-editor div.elementor-widget-container::text").getall()
            ).strip()
            if not addr_full:
                # A store with no listed address has no location information
                # to publish at all.
                continue

            yield self.parse_store(store, ref, branch, addr_full)

        page = response.meta["page"]
        if page < data["pagination"]["max_num_pages"]:
            yield self.make_request(page + 1)

    def parse_store(self, store, ref: str, branch: str, addr_full: str) -> Feature:
        # Strip a leading internal state-abbreviation tag, e.g. "(JH) ", that
        # is not part of the store's public-facing name (and is redundant
        # with the state derived below).
        branch = re.sub(r"^\s*\([A-Z]{2,4}\)\s*", "", branch).strip()

        item = Feature()
        item["ref"] = ref
        item["branch"] = branch
        item["addr_full"] = addr_full
        item["country"] = "MY"

        if state_match := re.search(r"\bstores_in_([a-z_]+)-", store.attrib.get("class", "")):
            item["state"] = MY_STATE_ISO_CODES.get(state_match.group(1))

        # The "Maps" button is a Google Maps "share this pin" URL where the
        # place name is itself the raw coordinate (e.g. "3°16'51.1"N ..."),
        # not a resolved address/business name, so this is the site
        # publishing a coordinate it already has rather than a live geocode.
        # A "maps.app.goo.gl"/"goo.gl" short link is left unresolved, since
        # that would require following a redirect to a geocoded place link.
        if maps_url := store.css("a.elementor-button::attr(href)").get():
            try:
                item["lat"], item["lon"] = url_to_coords(maps_url)
            except ValueError:
                pass

            if item.get("lat") is None and (m := LEGACY_COORD_PATTERN.search(unquote(maps_url))):
                item["lat"], item["lon"] = float(m.group(1)), float(m.group(2))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        return item
