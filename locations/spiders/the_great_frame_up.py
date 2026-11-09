from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class TheGreatFrameUpSpider(WPStoreLocatorSpider):
    """The shops are franchised and each keeps a site of its own, but the chain
    searches them all through the store locator its own site carries.

    The locator will not hand over everything at once - asked to, it answers
    with nothing - so the shops are found by searching a grid of points. It
    answers at most twenty five shops to any one search, and twenty five would
    mean some had been left out, so the radius is kept small enough that no
    search comes near it: the worst of them, over Chicago, returns fourteen.

    Note that the radius is counted in miles here rather than the kilometres
    the grid is spaced by, so each search reaches half again as far as it need
    to, and no part of the country is missed.
    """

    name = "the_great_frame_up"
    # Neither the chain nor any of its shops has a Wikidata item.
    item_attributes = {"brand": "The Great Frame Up"}
    allowed_domains = ["thegreatframeup.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 158
    max_results = 25
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # Each shop is named for the place it stands in, which is its branch
        # rather than a name of its own.
        item["branch"] = item.pop("name", None)

        # The address the chain gives for a shop is, for half of them, the
        # franchisee's own mailbox rather than the business's, so none is kept.
        item.pop("email", None)

        if isinstance(hours := item.get("opening_hours"), OpeningHours):
            item["opening_hours"] = self.daytime_only(hours)

        apply_category(Categories.SHOP_FRAME, item)
        yield item

    def daytime_only(self, hours: OpeningHours) -> OpeningHours:
        """Leave out any day whose hours would run on past midnight.

        A shop that frames pictures keeps shop hours, so a day that reads as a
        night shift is a slip of the pen rather than a day of trading. One shop
        states a Saturday of "10:00 pm - 4:00 pm", meaning ten in the morning.
        """
        daytime = OpeningHours()
        for day, ranges in hours.day_hours.items():
            for start, end in ranges:
                if (start.tm_hour, start.tm_min) < (end.tm_hour, end.tm_min):
                    daytime.add_range(day, start, end)
                else:
                    self.logger.warning(f"{day} reads as a night shift, so it is left out")
        for day in hours.days_closed:
            daytime.set_closed(day)
        return daytime
