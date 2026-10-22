import html
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours, day_range, sanitise_day
from locations.items import Feature

DAY = "|".join(DAYS_FULL)
TIME = r"\d{1,2}:\d{2}\s*[AP]M"
# A hyphen separates the days from the times and the times from each other, as well
# as joining a day range: "Monday - Saturday - 11:00 AM - 10:00 PM".
HOURS = re.compile(
    rf"(?P<days>(?:{DAY})(?:\s*(?P<joiner>[-–]|&|and)\s*(?:{DAY}))?)\s*[-–]\s*"
    rf"(?P<opens>{TIME})\s*[-–]\s*(?P<closes>{TIME})",
    re.IGNORECASE,
)
# Either "1405 Fort Crook Rd S" then "Bellevue, NE 68005", or both on one line.
LOCALITY = re.compile(r"^(?:(?P<street>.+),\s*)?(?P<city>[^,]+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})$")


class LaMesaMexicanRestaurantUSSpider(Spider):
    name = "la_mesa_mexican_restaurant_us"
    item_attributes = {"brand": "La Mesa Mexican Restaurant"}
    start_urls = ["https://la-mesa.com/locations/"]

    @staticmethod
    def lines(markup: str) -> list[str]:
        """Return a block's visible lines, which <br> separates rather than elements.

        The entities matter: one location writes "FRIDAY &amp; SATURDAY", and left
        encoded that day pair does not read as one.
        """
        parts = re.split(r"<br[^>]*>", markup)
        parts = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part))).strip() for part in parts]
        return [part for part in parts if part]

    def blurb(self, response: Response, header: str) -> list[str]:
        """Return the lines of the blurb module under the given heading."""
        for blurb in response.xpath('//div[contains(@class, "et_pb_blurb_content")]'):
            if blurb.xpath("normalize-space(.//h4[contains(@class, 'et_pb_module_header')])").get() == header:
                return self.lines(blurb.xpath('.//div[contains(@class, "et_pb_blurb_description")]').get(""))
        return []

    @staticmethod
    def hours(text: str) -> OpeningHours:
        oh = OpeningHours()
        for match in HOURS.finditer(text):
            labels = re.split(r"\s*(?:[-–]|&|and)\s*", match["days"], flags=re.IGNORECASE)
            days = [day for label in labels if (day := sanitise_day(label))]
            if len(days) == 2 and match["joiner"] in ("-", "–"):
                days = day_range(*days)
            for day in days:
                oh.add_range(
                    day, match["opens"].replace(" ", "").upper(), match["closes"].replace(" ", "").upper(), "%I:%M%p"
                )
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for link in response.xpath('//a[re:test(@href, "/locations/[^/]+/[^/]+/$")]'):
            branch = re.sub(r"\s*,\s*[A-Z]{2}$", "", link.xpath("normalize-space(.)").get(""))
            yield response.follow(
                link.xpath("@href").get(), callback=self.parse_location, cb_kwargs={"branch": branch or None}
            )

    def parse_location(self, response: Response, branch: str | None) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = branch

        # The St. Joseph page's title and description are a copy of the Bellevue
        # page's, so only its own Location block is trusted for the address.
        location = self.blurb(response, "Location")
        for line in location:
            if address := LOCALITY.match(line):
                item["street_address"] = address["street"] or item.get("street_address")
                item["city"] = address["city"]
                item["state"] = address["state"]
                item["postcode"] = address["postcode"]
            elif re.match(r"^\d", line):
                item["street_address"] = line
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)")

        hours = response.xpath('//div[contains(@class, "et_pb_text_inner")][h3[normalize-space()="Hours"]]').get()
        if hours:
            item["opening_hours"] = self.hours(" ".join(self.lines(hours)))

        # Of the advertised features only the patio maps to a tag, and it is claimed
        # only for the locations that list it.
        if any("Patio Seating" in feature for feature in self.blurb(response, "Features")):
            apply_yes_no("outdoor_seating", item, True)

        if pin := re.search(r"!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = pin.group(2), pin.group(1)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "mexican"
        yield item
