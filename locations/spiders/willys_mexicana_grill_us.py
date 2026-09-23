import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Location pages come from the site's locations sitemap. Each page marks the
# address up as a run of spans with segment-* classes, carries its coordinates
# on the map marker, and gives hours as a free text line such as
# "Mon-Sun 11:00am - 10:00pm".
#
# The amenity list marks the options a restaurant offers with a "check" class.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class WillysMexicanaGrillUSSpider(SitemapSpider):
    name = "willys_mexicana_grill_us"
    item_attributes = {"brand": "Willy's Mexicana Grill"}
    allowed_domains = ["willys.com"]
    sitemap_urls = ["https://willys.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        address = response.xpath("//address")
        if not address:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = response.xpath('//aside[@class="locations-bar"]/h2/text()').get()
        item["website"] = response.url
        item["housenumber"] = address.xpath('.//span[@class="segment-street_number"]/text()').get()
        item["street"] = address.xpath('.//span[@class="segment-street_name"]/text()').get()
        item["city"] = address.xpath('.//span[@class="segment-city"]/text()').get()
        item["state"] = address.xpath('.//span[@class="segment-state_short"]/text()').get()
        item["postcode"] = address.xpath('.//span[@class="segment-post_code"]/text()').get()
        item["phone"] = address.xpath('.//a[starts-with(@href, "tel:")]/text()').get()
        item["lat"] = response.xpath('//div[@class="marker"]/@data-lat').get()
        item["lon"] = response.xpath('//div[@class="marker"]/@data-lng').get()

        item["opening_hours"] = self.parse_opening_hours(
            response.xpath('//ul[@class="search-box-result-list"]/li[2]//p//text()').getall()
        )

        offered = {
            option.strip() for option in response.xpath('//ul[@class="list-box"]/li[@class="check"]/text()').getall()
        }
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in offered, False)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "Patio" in offered, False)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "mexican"

        yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """
        Parses lines such as "Mon-Sun 11:00am - 10:00pm". A few restaurants list
        temporary event hours first and then "Regular Business Hours: ...", in
        which case only the regular hours are read.
        """
        oh = OpeningHours()

        text = "\n".join(re.sub(r"\s+", " ", line).strip() for line in lines)
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        if (regular := text.lower().find("regular business hours")) != -1:
            text = text[regular:]

        for times in re.finditer(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", text, re.I):
            # The days are whatever day names directly precede the times.
            if not (
                days := re.search(
                    r"([A-Za-z]{3,9})(?:\s*-\s*([A-Za-z]{3,9}))?\s*:?\s*$", text[: times.start()].rstrip()
                )
            ):
                continue

            start, end = sanitise_day(days.group(1)), sanitise_day(days.group(2) or days.group(1))
            if not start or not end:
                continue

            oh.add_days_range(
                day_range(start, end),
                WillysMexicanaGrillUSSpider.normalise_time(times.group(1)),
                WillysMexicanaGrillUSSpider.normalise_time(times.group(2)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
