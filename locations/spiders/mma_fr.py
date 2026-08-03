import random
import re

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Matches e.g. "09h00 - 12h00" in the opening-hours HTML.
TIME_RANGE = re.compile(r"(\d{1,2}h\d{2})\s*-\s*(\d{1,2}h\d{2})")


class MmaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mma_fr"
    item_attributes = {"brand": "MMA", "brand_wikidata": "Q3331046"}
    sitemap_urls = ["https://agence.mma.fr/home.sitemap.xml"]
    # Used by get_ref(); JSON-LD has no stable identifier of its own.
    sitemap_rules = [(r"/([\w-]+)/$", "parse")]
    custom_settings = {
        "DOWNLOAD_DELAY": 5,  # robots.txt specifies Crawl-delay: 5.
    }

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        # Overridden from HTML below; the framework can't parse MMA's
        # space-separated multi-range format ("09:00-12:00 14:00-17:30").
        ld_data.pop("openingHours", None)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        # JSON-LD "name" is a generic template; the real trading name, when
        # different, is only in the page's own HTML.
        item.pop("name", None)
        if title := response.css("h2.title::text").get():
            name = re.sub(r"\bMMA\b", "", title, flags=re.I)
            name = re.sub(r"\s+", " ", name).strip(" -")
            item["branch"] = name.title()

        # Source addresses are SHOUTING CASE.
        if item.get("street_address"):
            item["street_address"] = item["street_address"].title()
        if item.get("city"):
            item["city"] = item["city"].title()

        # Monaco shares France's "98" postcode prefix; override the FR
        # default this spider's name suffix otherwise implies.
        if (item.get("postcode") or "").startswith("980"):
            item["country"] = "MC"

        # Placeholder image: literal "null" string, or MMA's no-photo avatar.
        image = item.get("image") or ""
        if image == "null" or "AgenceDefault" in image:
            item["image"] = None

        # "sameAs" is MMA's generic corporate Facebook page on every agency.
        if item.get("facebook") == "https://www.facebook.com/MMA.Assurances":
            item["facebook"] = None

        # JSON-LD only lists open days; parse from HTML to also capture
        # explicit closed days.
        item["opening_hours"] = self.parse_opening_hours(response)

        # A small, stable set of pages (<0.5%) always come back missing one
        # of these fields - a permanent MMA data gap, not a transient
        # failure, but retrying is cheap insurance against a real one.
        if not all([item.get("city"), item.get("phone"), item.get("opening_hours"), item.get("lat"), item.get("lon")]):
            if response.request is not None:
                if retry := get_retry_request(
                    response.request,
                    spider=self,
                    max_retry_times=3,
                    reason="missing city, phone, opening hours, or geometry",
                    priority_adjust=random.randint(-20, -1),
                ):
                    retry.meta["dont_cache"] = True  # Don't replay the bad response.
                    yield retry
                    return

        # NSI's entry restricts locationSet to "fx", which never matches
        # this spider's "fr" country code, so apply the category manually.
        apply_category(Categories.OFFICE_INSURANCE, item)

        yield item

    @staticmethod
    def parse_opening_hours(response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        for day_row in response.css("#opening-hours-full li.item"):
            day_fr = day_row.css("span.day::text").get()
            day = DAYS_FR.get((day_fr or "").strip())
            if not day:
                continue
            if "disabled" in (day_row.attrib.get("class") or "").split():
                oh.set_closed(day)
                continue
            for span_text in day_row.css("span:not(.day)::text").getall():
                if m := TIME_RANGE.search(span_text):
                    open_time, close_time = (t.replace("h", ":") for t in m.groups())
                    oh.add_range(day, open_time, close_time)
                # Non-time text (e.g. "sur RDV") is silently skipped.
        return oh
