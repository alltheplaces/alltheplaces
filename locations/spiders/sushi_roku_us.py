import html
import re
from datetime import datetime

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours, day_range, sanitise_day
from locations.structured_data_spider import StructuredDataSpider

# The service blocks that open the page ("Lunch", "Dinner", "Lunch & Dinner") carry
# the regular hours. Everything from the first of these headings onwards is either a
# promotion, a one-off event or practical advice, none of which is opening hours.
IGNORE_FROM = re.compile(r"(?i)\b(happy hour|parking|proper attire|private event|race weekend|reservations?)\b")
TIME_RANGE = re.compile(
    r"(\d{1,2}(?::\d{2})?)\s*([AP]\.?M\.?)?\s*[-–—]\s*(\d{1,2}(?::\d{2})?)\s*([AP]\.?M\.?)?",
    re.IGNORECASE,
)


class SushiRokuUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sushi_roku_us"
    item_attributes = {"brand": "Sushi Roku", "brand_wikidata": "Q7648921"}
    sitemap_urls = ["https://www.sushiroku.com/sitemap.xml"]
    sitemap_rules = [(r"/location/[^/]+/$", "parse_sd")]
    wanted_types = ["FoodEstablishment"]

    @staticmethod
    def lines(markup: str) -> list[str]:
        """Return the visible lines of the hours block, which <br> separates rather than elements."""
        parts = re.split(r"<br[^>]*>|</p>", markup)
        parts = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part))) for part in parts]
        # The pages pepper their headings with zero-width joiners.
        return [part.replace("\u200d", "").strip(" |\u00a0") for part in parts]

    @staticmethod
    def days(spec: str) -> list[str]:
        """Resolve a day label such as "Sunday -Thursday", "Friday & Saturday" or "Daily"."""
        if not (spec := spec.strip(" |,")):
            return []
        if re.fullmatch(r"(?i)daily|every ?day|7 days", spec):
            return [sanitise_day(day) for day in DAYS_FULL]
        if parts := re.split(r"\s*[-–]\s*", spec):
            if len(parts) == 2 and (start := sanitise_day(parts[0])) and (end := sanitise_day(parts[1])):
                return day_range(start, end)
        found = [sanitise_day(part) for part in re.split(r"\s*(?:&|and|,)\s*", spec)]
        return found if found and all(found) else []

    @staticmethod
    def normalise(time: str, meridiem: str | None, fallback: str | None) -> str | None:
        """Pin a meridiem onto a time, since the pages often write only the closing one."""
        if not (meridiem := (meridiem or fallback)):
            return None
        if ":" not in time:
            time = f"{time}:00"
        return f"{time}{meridiem.replace('.', '').upper()}"

    def hours(self, markup: str) -> OpeningHours:
        oh = OpeningHours()
        current = []
        for line in self.lines(markup):
            if not line:
                continue
            if IGNORE_FROM.search(line):
                break
            if not (times := TIME_RANGE.search(line)):
                # A bare day label applies to the service lines that follow it.
                if days := self.days(line):
                    current = days
                continue
            opens_at, opens_meridiem, closes_at, closes_meridiem = times.groups()
            opens = self.normalise(opens_at, opens_meridiem, closes_meridiem)
            closes = self.normalise(closes_at, closes_meridiem, opens_meridiem)
            if not opens or not closes:
                continue
            if (start := datetime.strptime(opens, "%I:%M%p")) >= datetime.strptime(closes, "%I:%M%p"):
                # "11:30-2:00PM" is a lunch service, not a shift that ends the next afternoon.
                opens = start.strftime("%I:%M") + ("AM" if opens.upper().endswith("PM") else "PM")
            if days := self.days(line[: times.start()]):
                current = days
            for day in current:
                oh.add_range(day, opens, closes, time_format="%I:%M%p")
        return oh

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item.pop("name", None)
        item["website"] = response.url
        # The Santa Monica page publishes no address at all, and empty strings
        # reach us as "" rather than as missing keys.
        for field in ("street_address", "city", "state", "postcode"):
            if not (item.get(field) or "").strip():
                item[field] = None

        map_block = response.xpath("//div[@data-gmaps-lat and @data-gmaps-lng]")
        item["lat"] = map_block.xpath("@data-gmaps-lat").get()
        item["lon"] = map_block.xpath("@data-gmaps-lng").get()
        if place_id := map_block.xpath("@data-gmaps-place-id").get():
            item["extras"]["ref:google:place_id"] = place_id

        if intro := response.xpath('//section[@id="intro"]').get():
            item["opening_hours"] = self.hours(intro)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "sushi;japanese"
        yield item
