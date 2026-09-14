import html
import re
from typing import Any, AsyncIterator
from urllib.parse import unquote

from scrapy import Request, Spider
from scrapy.http import Response

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

    def make_request(self, page: int) -> Request:
        return Request(
            f"https://99speedmart.com.my/store-locations/?e-page-a09cddc={page}",
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The site's own "wp-json/wp/v2/stores" REST API looks like a clean
        # data source, but its "acf" field (address/maps) is empty for ~80%
        # of records even though the same records render with full address
        # and map data on this listing page. So the store-locations listing
        # itself (paginated via ?e-page-a09cddc=N) is scraped instead, since
        # it is the only place this data is reliably complete.
        seen_refs = response.meta.get("seen_refs", set())

        for store in response.css("div.e-loop-item"):
            title = html.unescape(" ".join(store.css("p.elementor-heading-title::text").getall())).strip()
            if not title or "–" not in title:
                continue

            ref, _, branch = title.partition("–")
            ref = ref.strip()
            if ref in seen_refs:
                # The same store can appear twice on a page (once in a
                # "recently opened" carousel, once in the main grid), and a
                # handful of stores have an accidental duplicate post with an
                # identical address published under the same store number.
                continue

            addr_full = " ".join(
                store.css("div.elementor-widget-text-editor div.elementor-widget-container::text").getall()
            ).strip()
            if not addr_full:
                # A store with no listed address has no location information
                # to publish at all.
                continue
            seen_refs.add(ref)

            yield self.parse_store(store, ref, branch, addr_full)

        if response.css("div.e-load-more-anchor"):
            max_page = int(response.css("div.e-load-more-anchor::attr(data-max-page)").get())
            page = response.meta["page"]
            if page < max_page:
                next_request = self.make_request(page + 1)
                next_request.meta["seen_refs"] = seen_refs
                yield next_request

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
