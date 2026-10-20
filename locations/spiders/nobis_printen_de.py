import base64
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import CLOSED_DE, DAYS_DE, OpeningHours
from locations.items import Feature


class NobisPrintenDESpider(SitemapSpider):
    name = "nobis_printen_de"
    item_attributes = {"brand": "Nobis", "brand_wikidata": "Q1994827", "state": "DE-NW"}
    sitemap_urls = ["https://nobis-printen.de/avada_portfolio-sitemap.xml"]
    sitemap_rules = [(r"/baeckerei/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not response.css(".nobis-branch-info"):
            return

        item = Feature()
        item["ref"] = response.css("body::attr(class)").re_first(r"postid-(\d+)")
        item["website"] = response.url

        item["street_address"] = response.css(".nobis-address__street::text").get("").strip()
        locality = response.css(".nobis-address__locality::text").get("").strip()
        if m := re.match(r"(\d{5})\s+(.+)", locality):
            item["postcode"], item["city"] = m.group(1), m.group(2)

        # The Google Maps embed is hidden behind a Borlabs Cookie consent
        # blocker, so the iframe HTML is only available base64-encoded in a
        # data attribute rather than as a live iframe src.
        if map_blob := response.css(
            "[data-borlabs-cookie-content-blocker-id=google-maps]::attr(data-borlabs-cookie-content)"
        ).get():
            decoded = base64.b64decode(map_blob).decode()
            if src := re.search(r'src="([^"]+)"', decoded):
                item["lat"], item["lon"] = url_to_coords(src.group(1))

        days = response.css(".nobis-hours__day::text").getall()
        times = response.css(".nobis-hours__time::text").getall()
        hours_string = ", ".join(f"{day.strip()} {time.strip()}" for day, time in zip(days, times))
        oh = OpeningHours()
        oh.add_ranges_from_string(hours_string, days=DAYS_DE, closed=CLOSED_DE)
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_BAKERY, item)

        yield item
