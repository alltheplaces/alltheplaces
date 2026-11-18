import re
from typing import Any, Iterable

from scrapy import Selector
from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import NAMED_DAY_RANGES_EN, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# Ocean Prime, the group's national chain, is gathered from its own site by
# spider `ocean_prime_us`, so its restaurants are not taken a second time here.
SEPARATE_SPIDER = {"ocean prime"}

# Two of the group's venues are not restaurants: one is a hall let to
# independent kitchens, the other a cigar lounge inside one of the restaurants.
CATEGORIES = {
    "Budd Dairy Food Hall": {"amenity": "food_court"},
    "The Rock Cigar Club": Categories.BAR,
}

# The last line of an address ends with the town, the state and the postcode:
# "Columbus, Ohio 43215". The state is spelled out as often as it is written as
# a code, and whatever stands before the town shares the line with it.
ADDRESS = re.compile(r"^(?P<lead>.+?)\s*,\s*(?P<state>[A-Za-z.]+(?:\s[A-Za-z.]+)*?)\s+(?P<postcode>\d{5})(?:-\d{4})?$")
# A street run together with its town, no comma between them, as "1500 Polaris
# Parkway Columbus".
RUN_ON = re.compile(
    r"^(?P<street>\d.*\b(?:Avenue|Ave|Boulevard|Blvd|Circle|Cir|Commons|Court|Ct|Crossing|Drive"
    r"|Dr|Highway|Hwy|Lane|Ln|Parkway|Pkwy|Place|Pl|Plaza|Road|Rd|Square|Station|Street|St"
    r"|Terrace|Way)\.?)\s+(?P<city>[A-Z].*)$"
)
# "Monday - Thursday | 4 PM - 10 PM", and also "Daily | 4 - 6 PM", where the
# meridiem is stated once, and "Monday - Friday 7 AM - 11 AM", with nothing
# between the days and the times at all.
HOURS = re.compile(
    r"(?P<days>.*?)\s*[|,]?\s*(?P<opens>\d{1,2}(?::\d{2})?)\s*(?P<opens_meridiem>[AP]\.?M\.?)?"
    r"\s*-\s*(?P<closes>\d{1,2}(?::\d{2})?)\s*(?P<closes_meridiem>[AP]\.?M\.?)",
    re.IGNORECASE,
)
# Hours given under one of these headings are a promotion served within the
# trading hours rather than hours of their own.
NOT_TRADING = re.compile(r"happy hour|social hour", re.IGNORECASE)
EVERY_DAY = re.compile(r"every\s*day", re.IGNORECASE)
ALL_WEEK = NAMED_DAY_RANGES_EN["Daily"]
# The link to a venue's own page, as the site labels it, best first.
OWN_PAGE = ("Learn More", "Visit Website", "View Menus")
REDIRECTS = [301, 302, 303, 307, 308]


class CameronMitchellRestaurantsSpider(SitemapSpider):
    """The group gives each of its restaurant brands a page, and that page
    states every one of that brand's restaurants in full.

    No coordinates are published as such. Each restaurant instead links itself
    on Google Maps, and most of those links are shortened, so they are asked
    for their redirect and the position read out of where they point. A few
    are written out in full and state the position already.
    """

    name = "cameron_mitchell_restaurants"
    item_attributes = {"operator": "Cameron Mitchell Restaurants", "operator_wikidata": "Q5026316"}
    # The shortened map links are resolved against Google's own hosts.
    allowed_domains = ["cameronmitchell.com", "maps.app.goo.gl", "goo.gl"]
    sitemap_urls = ["https://cameronmitchell.com/restaurant-brand-sitemap.xml"]
    sitemap_rules = [(r"/restaurants/[^/]+/$", "parse_brand")]

    def parse_brand(self, response: Response) -> Iterable[Any]:
        for venue in response.css(".r-location"):
            # Each brand is its own name, and the restaurant is named for the
            # place it stands in.
            brand = self.plain(venue.css(".article-title h3 span::text").get())
            if brand.casefold() in SEPARATE_SPIDER:
                continue

            item = Feature()
            item["brand"] = brand or None
            item["branch"] = self.plain(" ".join(venue.css(".article-title h3::text").getall()))
            item["website"] = item["ref"] = self.own_page(venue)
            item["image"] = venue.css("img.l-photo::attr(src)").get()
            if phone := venue.css('.r-phone a[href^="tel:"]::attr(href)').get():
                item["phone"] = phone.removeprefix("tel:").strip()

            self.parse_address(item, venue)
            item["opening_hours"] = self.parse_hours(venue)

            apply_category(CATEGORIES.get(brand, Categories.RESTAURANT), item)

            directions = venue.css("a.lnk-directions::attr(href)").get() or ""
            if position := self.position(directions):
                item["lat"], item["lon"] = position
                yield item
            elif "goo.gl" in directions:
                # A shortened link carries no position itself, so it is asked
                # where it points. Two of the venues share a building, and so
                # share a link, which is why the request is not deduplicated.
                yield Request(
                    directions,
                    method="HEAD",
                    callback=self.parse_position,
                    cb_kwargs={"item": item},
                    dont_filter=True,
                    meta={"dont_redirect": True, "handle_httpstatus_list": REDIRECTS},
                )
            else:
                # One restaurant links its booking service rather than a map,
                # and another a map bearing no position.
                self.logger.info(f"{item['branch']} states no position, so it is published without one")
                yield item

    def parse_position(self, response: Response, item: Feature) -> Iterable[Feature]:
        points_at = response.headers.get("Location")
        if position := self.position(points_at.decode() if points_at else ""):
            item["lat"], item["lon"] = position
        else:
            self.logger.warning(f"No position in the map link for {item['branch']}")
        yield item

    @staticmethod
    def plain(value: str | None) -> str:
        """Return a name with a typewriter's apostrophe rather than a typesetter's."""
        return re.sub(r"\s+", " ", (value or "").replace("’", "'")).strip()

    @staticmethod
    def position(url: str) -> tuple[float, float] | None:
        """Return the position a Google Maps URL states, if it states one."""
        if not url:
            return None
        try:
            coords = url_to_coords(url)
        except ValueError:
            return None
        return coords if coords != (None, None) else None

    @staticmethod
    def own_page(venue: Selector) -> str | None:
        """Return the link to the restaurant's own page.

        A brand of one restaurant links the front of its site, a brand of
        several links the part of it given to that one. Both are reached by way
        of the menus, which sit a step below the page wanted.
        """
        pages = {
            " ".join(link.css("::text").getall()).strip(): (link.css("::attr(href)").get() or "").strip()
            for link in venue.css(".l-links a")
        }
        for label in OWN_PAGE:
            if page := pages.get(label):
                return page.removesuffix("menus/").rstrip() or None
        return None

    def parse_address(self, item: Feature, venue: Selector) -> None:
        """Take the address apart.

        It is written as a line or three, the last of them carrying the town,
        the state and the postcode. Everything above that is the street, which
        for about a third of them is led by the name of the building or square
        the restaurant stands in.
        """
        lines = [
            re.sub(r"\s+", " ", line).strip(" () ").strip().rstrip(",") for line in venue.css("address::text").getall()
        ]
        lines = [line for line in lines if line]
        if not lines or not (stated := ADDRESS.match(lines[-1])):
            self.logger.warning(f"Unparsed address {lines} for {item.get('branch')}")
            return

        street = lines[:-1]
        lead = stated["lead"]
        if "," in lead:
            # The street shares the line with the town: "155 East Broad
            # Street, Columbus".
            head, city = lead.rsplit(",", 1)
            street.append(head.strip())
        elif run_on := RUN_ON.match(lead):
            # The two were written with no comma to divide them.
            street.append(run_on["street"])
            city = run_on["city"]
        else:
            city = lead

        item["street_address"] = merge_address_lines(street)
        item["city"] = city.strip()
        # Washington writes its state with full stops, and the rest are either
        # a code already or spelled out for the pipeline to shorten.
        state = stated["state"].strip()
        item["state"] = state.replace(".", "") if len(state.replace(".", "")) == 2 else state
        item["postcode"] = stated["postcode"]
        item["country"] = "US"

    def parse_hours(self, venue: Selector) -> OpeningHours | None:
        """Read the hours, which are set out a meal at a time.

        Each heading names a service - breakfast, lunch, brunch, dinner - and
        the lines beneath it give the days and the times it is served. A
        restaurant open for more than one of them states each separately, so
        the hours of a day are gathered from every service it serves.
        """
        oh = OpeningHours()
        for heading in venue.css(".l-hours h3"):
            named = " ".join(heading.css("::text").getall()).strip()
            if NOT_TRADING.search(named):
                continue
            for line in heading.xpath("following-sibling::p[1]/text()").getall():
                line = re.sub(r"\s+", " ", line).replace("–", "-").replace("—", "-").strip()
                if not line:
                    continue
                if not (stated := HOURS.search(line)):
                    # Several carry a note rather than hours, and one states a
                    # closing time of "Close".
                    if re.search(r"\d", line):
                        self.logger.info(f"Unparsed hours {line!r} under {named!r}")
                    continue
                if not (days := self.parse_days(stated["days"])):
                    self.logger.warning(f"Unparsed days in {line!r} under {named!r}")
                    continue
                opens, closes = self.parse_times(stated)
                for day in days:
                    oh.add_range(day, opens, closes, time_format="%I:%M%p")

        return self.merge(oh) if oh.as_opening_hours() else None

    @staticmethod
    def parse_days(stated: str) -> list[str]:
        days: list[str] = []
        for token in re.split(r"&|,|\band\b", stated.strip(" |,")):
            if not (token := token.strip(" |.")):
                continue
            if named := NAMED_DAY_RANGES_EN.get(token.title()):
                days.extend(named)
            elif EVERY_DAY.fullmatch(token):
                days.extend(ALL_WEEK)
            elif "-" in token:
                start, end = (sanitise_day(part) for part in token.split("-", 1))
                if start and end:
                    days.extend(day_range(start, end))
            elif day := sanitise_day(token):
                days.append(day)
        return days

    @staticmethod
    def parse_times(stated: re.Match) -> tuple[str, str]:
        def clock(value: str, meridiem: str) -> str:
            return f"{value if ':' in value else value + ':00'}{meridiem}"

        closes_meridiem = stated["closes_meridiem"].replace(".", "").upper()
        opens_meridiem = (stated["opens_meridiem"] or "").replace(".", "").upper()
        if not opens_meridiem:
            # The meridiem is stated once, at the end of the range, so an
            # opening hour later than the closing hour is in the morning -
            # except for noon, which stays where it is.
            opens_hour, closes_hour = (int(stated[part].split(":")[0]) for part in ("opens", "closes"))
            opens_meridiem = (
                "AM" if closes_meridiem == "PM" and opens_hour != 12 and opens_hour > closes_hour else closes_meridiem
            )
        return clock(stated["opens"], opens_meridiem), clock(stated["closes"], closes_meridiem)

    @staticmethod
    def merge(hours: OpeningHours) -> OpeningHours:
        """Draw the services of a day together into the hours it keeps.

        Lunch running to four and dinner starting at four are one unbroken
        afternoon, and are stated as such rather than as two sittings.
        """
        merged = OpeningHours()
        for day, ranges in hours.day_hours.items():
            spans: list[list[int]] = []
            for start, end in sorted(
                (start.tm_hour * 60 + start.tm_min, end.tm_hour * 60 + end.tm_min) for start, end in ranges
            ):
                if spans and start <= spans[-1][1]:
                    spans[-1][1] = max(spans[-1][1], end)
                else:
                    spans.append([start, end])
            for start, end in spans:
                merged.add_range(day, f"{start // 60:02}:{start % 60:02}", f"{end // 60:02}:{end % 60:02}")
        for day in hours.days_closed:
            merged.set_closed(day)
        return merged
