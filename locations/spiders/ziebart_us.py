import re
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Location pages come from the site's sitemap. Each page holds the address
# inside its Google Maps embed URL, the phone in a tel: link, and the hours as
# two columns, one of day labels and one of times.
#
# Every page also carries a "preferred store" widget for whichever store the
# visitor last used, which repeats another store's address and code, so the
# store's own details are read from the location map block and the URL.
#
# Coordinates are only present when the page links to a Google Maps place with
# an "@lat,lng" URL; some pages link to an address search instead, and those
# features have no geometry.


class ZiebartUSSpider(SitemapSpider):
    name = "ziebart_us"
    item_attributes = {"brand": "Ziebart", "brand_wikidata": "Q8071501"}
    allowed_domains = ["www.ziebart.com"]
    sitemap_urls = ["https://www.ziebart.com/sitemap.xml"]
    sitemap_rules = [(r"/find-my-ziebart/location/([^/]+)$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The page also carries a "preferred store" widget for whichever store
        # the visitor last used, so the store's own map and code are taken from
        # the location map block and the URL rather than the first match.
        address = unquote(
            response.xpath('//div[contains(@class, "location-google-map")]//iframe/@src').re_first(r"[?&]q=(.+)$")
            or ""
        ).replace("+", " ")
        if not (parts := re.fullmatch(r"(.+),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})", address.strip())):
            return

        slug = response.url.rstrip("/").rsplit("/", 1)[-1]

        item = Feature()
        item["ref"] = slug.split("-", 1)[0].upper()
        item["branch"] = (response.xpath("//h1//text()").getall()[1:2] or [""])[0].strip() or None
        item["website"] = response.url
        item["street_address"], item["city"], item["state"], item["postcode"] = parts.groups()
        item["phone"] = response.xpath('//a[@class="location-phone"]/@data-original-number').get()

        # Only some of the map links carry coordinates; the rest are address
        # searches.
        for place in response.xpath('//a[contains(@href, "google.com/maps/place")]/@href').getall():
            if coordinates := re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", unquote(place)):
                item["lat"], item["lon"] = coordinates.groups()
                break

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours | None:
        """The hours are two columns: "Mon - Fri:" / "7:45 am - 5:30 pm"."""
        oh = OpeningHours()

        for row in response.xpath('//div[contains(@class, "row")][.//p[contains(text(), "Mon")]]'):
            values = [value.strip() for value in row.xpath(".//p/text()").getall()]
            labels = [value for value in values if value.endswith(":")]
            times = [value for value in values if value and not value.endswith(":")]

            for label, time in zip(labels, times):
                days = []
                for token in re.split(r"&|,|\band\b", label.rstrip(":")):
                    token = token.strip()
                    if "-" in token:
                        start, end = [sanitise_day(part) for part in token.split("-", 1)]
                        if start and end:
                            days.extend(day_range(start, end))
                    elif day := sanitise_day(token):
                        days.append(day)

                if not days:
                    continue
                if rule := re.fullmatch(r"(\d{1,2}:\d{2}\s*[ap]m)\s*-\s*(\d{1,2}:\d{2}\s*[ap]m)", time, re.I):
                    oh.add_days_range(
                        days,
                        rule.group(1).replace(" ", "").upper(),
                        rule.group(2).replace(" ", "").upper(),
                        time_format="%I:%M%p",
                    )
            break

        return oh if oh else None
