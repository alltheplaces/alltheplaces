import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# Parry's publishes one page per location, but two page templates are in use and
# they expose different things:
#
#   * the older template marks the address up with schema.org microdata and
#     links the phone number with a tel: URL, but has no coordinates, and
#   * the newer template has an embedded Google map carrying coordinates, with
#     the address, phone and hours written as plain paragraphs that are only
#     identifiable by the icon image each one starts with.
#
# Both are parsed below. No brand:wikidata is set because the chain has no
# Wikidata item.


class ParrysPizzeriaAndBarUSSpider(SitemapSpider):
    name = "parrys_pizzeria_and_bar_us"
    item_attributes = {"brand": "Parry's Pizzeria & Taphouse"}
    allowed_domains = ["parryspizza.com"]
    sitemap_urls = ["https://parryspizza.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.strip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["branch"] = self.parse_branch(response)

        if response.xpath('//*[@itemprop="streetAddress"]'):
            self.parse_microdata_template(item, response)
        else:
            self.parse_map_template(item, response)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item

    @staticmethod
    def parse_branch(response: Response) -> str | None:
        if not (heading := response.xpath("//h1/text()").get()):
            return None
        # Headings are either "Arvada" or "Brownsville, TX".
        return re.sub(r",\s*[A-Z]{2}$", "", heading.strip()) or None

    @staticmethod
    def parse_microdata_template(item: Feature, response: Response) -> None:
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["city"] = response.xpath('//*[@itemprop="addressLocality"]/text()').get()
        item["state"] = response.xpath('//*[@itemprop="addressRegion"]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').get()

        hours = response.xpath('//h3[.//i[contains(@class, "fa-clock-o")]]/following-sibling::p[1]//text()').getall()
        item["opening_hours"] = ParrysPizzeriaAndBarUSSpider.parse_opening_hours(hours)

    @staticmethod
    def parse_map_template(item: Feature, response: Response) -> None:
        if coordinates := re.search(r"!2d(-?[\d.]+)!3d(-?[\d.]+)", response.text):
            item["lon"], item["lat"] = coordinates.groups()

        address = ParrysPizzeriaAndBarUSSpider.icon_paragraph(response, "Pin")
        if len(address) >= 2:
            # "2320 North Expy, Suite 3" / "Brownsville, TX 78521"
            item["street_address"] = address[0]
            if locality := re.match(r"(.+),\s*([A-Z]{2})\s*(\d{5})", address[1]):
                item["city"], item["state"], item["postcode"] = locality.groups()
        else:
            item["addr_full"] = merge_address_lines(address)

        if phone := ParrysPizzeriaAndBarUSSpider.icon_paragraph(response, "Phone"):
            item["phone"] = phone[0]

        item["opening_hours"] = ParrysPizzeriaAndBarUSSpider.parse_opening_hours(
            ParrysPizzeriaAndBarUSSpider.icon_paragraph(response, "Hours")
        )

    @staticmethod
    def icon_paragraph(response: Response, alt: str) -> list[str]:
        """Returns the text of the paragraph introduced by the named icon image."""
        lines = response.xpath(f'//p[.//img[@alt="{alt}"]]//text()').getall()
        return [line for line in map(str.strip, lines) if line]

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """Parses rules such as "Sunday-Thursday: 11am-10pm" and "Friday & Saturday: 11am to 12am"."""
        oh = OpeningHours()

        for line in lines:
            line = line.replace("\u2013", "-").replace("\u2014", "-").replace(" to ", "-")
            if not (times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I)):
                continue

            # Some pages separate the days from the times with a colon, some
            # with only a space.
            days = []
            for token in re.split(r"&|\band\b", line[: times.start()].rstrip(": ")):
                # "Sunday (through Oct. 25)" carries a temporary note.
                token = re.sub(r"\(.*?\)", "", token).strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        days.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    days.append(day)

            if days:
                oh.add_days_range(
                    days,
                    ParrysPizzeriaAndBarUSSpider.normalise_time(times.group(1)),
                    ParrysPizzeriaAndBarUSSpider.normalise_time(times.group(2)),
                    time_format="%I:%M%p",
                )

        return oh if oh.as_opening_hours() else None

    @staticmethod
    def normalise_time(value: str) -> str:
        """Turns "11am", "9:45 am" into a consistent "%I:%M%p" string."""
        value = value.replace(" ", "").lower()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
