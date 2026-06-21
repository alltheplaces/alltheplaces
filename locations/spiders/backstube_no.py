import re
from urllib.parse import unquote

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BackstubeNOSpider(Spider):
    name = "backstube_no"
    item_attributes = {"brand": "Backstube", "country": "NO"}
    start_urls = ["https://backstube.no/visit-us"]

    def parse(self, response: Response):
        for location in response.css(".location-row"):
            name = location.css(".location-info strong::text").get()
            if not name:
                continue
            name = name.strip()

            item = Feature()
            item["ref"] = re.sub(r"\W+", "-", name.lower())
            item["name"] = "Backstube"
            item["branch"] = name
            item["website"] = "https://backstube.no/visit-us"
            item["street_address"] = location.css(".location-info::text").get().strip()

            hours = location.css(".location-hour div::text").getall()
            if hours:
                item["opening_hours"] = OpeningHours()
                hours_string = "; ".join([h.strip() for h in hours if h.strip()])
                item["opening_hours"].add_ranges_from_string(hours_string)

            apply_category(Categories.SHOP_BAKERY, item)

            map_href = location.css(".location-link a::attr(href)").get()
            if map_href and "maps.app.goo.gl" in map_href:
                yield Request(
                    map_href,
                    callback=self._parse_short_link,
                    cb_kwargs={"item": item},
                    dont_filter=True,
                )
            else:
                yield item

    def _parse_short_link(self, response: Response, item: Feature):
        final_url = response.url
        m = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", unquote(final_url))
        if not m:
            for redirect in response.meta.get("redirect_urls", []):
                m = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", unquote(redirect))
                if m:
                    break
        if m:
            item["lat"] = float(m.group(1))
            item["lon"] = float(m.group(2))
        yield item
