import random
import re

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class GmfFRSpider(SitemapSpider):
    name = "gmf_fr"
    item_attributes = {"brand": "GMF", "brand_wikidata": "Q3095296"}
    # No dedicated agency sitemap (unlike MAAF's sitemap-agences.xml) - agency
    # pages are mixed into the site's general sitemap alongside ~1500
    # unrelated content/product pages, filtered out by sitemap_rules below.
    sitemap_urls = ["https://www.gmf.fr/accueil.sitemap.xml"]
    # Agency pages are "/agences-gmf/assurance-<slug>" (singular). The same
    # sitemap also lists ~104 department/region pages under
    # "/agences-gmf/assurances-<Departement>-<code>" (plural) - the trailing
    # "-" in this pattern deliberately excludes those, since "assurances-"
    # never matches "assurance-" followed by a literal hyphen.
    sitemap_rules = [(r"/agences-gmf/assurance-([\w-]+)$", "parse")]
    # A handful of "assurance-<slug>" URLs matching the pattern above are not
    # agency pages at all - see NOT_AN_AGENCY_PAGE_SIZE in parse() below for
    # why and how that's detected.
    #
    # Site is behind DataDome (confirmed via "x-datadome: protected" response
    # header on agency pages - the sitemap itself is not blocked). A direct
    # Zyte API test initially succeeded with plain httpResponseBody automap,
    # but a real crawl showed that was a fluke: subsequent attempts (even a
    # single, isolated one after a cooldown) were consistently banned.
    # browserHtml reliably gets through where httpResponseBody does not -
    # same DataDome-protected Covéa group site, same fix as
    # locations/spiders/maaf_fr.py (requires_proxy alone is not enough here
    # either, hence not set - it only automaps to httpResponseBody).
    custom_settings = {
        # A first test run at the project's default concurrency got banned
        # on essentially every single request (both with browserHtml and
        # with the simpler httpResponseBody automap) - a much higher ban
        # rate than a handful of manual, well-spaced requests had suggested.
        # Lowering concurrency and adding a delay between requests to this
        # one domain got a real crawl to 100% success (23/23 Zyte requests,
        # 19/19 items) - kept deliberately conservative rather than pushed
        # back up, since browserHtml requests are already slow (~13s each
        # observed) and there is no throughput need to justify the risk of
        # tripping the ban behaviour again.
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    # Threshold used in parse() to tell a genuine "not an agency page" apart
    # from an incomplete render - see the comment there for the full
    # reasoning. Measured on a real, complete agency page: h1.geo-title/
    # .geo-agency sit at a near-constant ~48KB into the document (agen:
    # 48048, arras: 48034 - just 14 bytes apart, so driven by shared
    # template/header content rather than anything agency-specific), and a
    # full crawl of all 325 sitemap agency URLs on 2026-08-05 found a clean
    # gap in body sizes with no page of any kind between ~10KB and ~70KB:
    # every incomplete render was under 10KB, every disambiguation page
    # (see below) was over 75KB. 60KB sits in that empty gap, comfortably
    # past the marker's position and comfortably short of the smallest
    # disambiguation page found.
    NOT_AN_AGENCY_PAGE_SIZE = 60_000

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {
                "browserHtml": True,
                "geolocation": "FR",
                "javascript": True,
            }
            yield request

    def parse(self, response: TextResponse, **kwargs):
        # No JSON-LD at all on this site, and the microdata present has a
        # nesting bug: the "geo" GeoCoordinates block sits inside a
        # <div itemscope itemtype=".../Place"> that itself carries no
        # itemprop, so it is never actually attached to the enclosing
        # Organization item. A generic microdata parser would therefore
        # produce two disconnected items instead of one usable Feature, so
        # this spider extracts everything by hand via XPath/CSS instead of
        # StructuredDataSpider - same approach as locations/spiders/cic_fr.py
        # for a similar French microdata site.
        name = response.css("h1.geo-title::text, h1.group-title::text").get()
        if not name:
            # Two different things can cause this, and they need opposite
            # handling:
            #  1. A genuinely incomplete render (Zyte ban noise slipping
            #     through as a 200 with an empty/challenge body) - retry.
            #  2. A handful of "assurance-<slug>" URLs are not agency pages
            #     at all: for a city served by more than one GMF agency, the
            #     bare city-name slug (e.g. "assurance-paris",
            #     "assurance-lyon") is a search-results/disambiguation page
            #     listing every agency in that city (each already covered
            #     separately in the sitemap under its own suffixed slug,
            #     e.g. "paris-bastille"), not an agency record itself. This
            #     is permanent - retrying gets the exact same listing page
            #     every time, wasting 5 attempts on something that will
            #     never become an agency record.
            # Both look identical from "no h1.geo-title" alone. The
            # difference is body size: a real agency page's own heading
            # always sits at a near-constant offset into the document (see
            # NOT_AN_AGENCY_PAGE_SIZE), so a response already well past that
            # point with still no heading cannot be a truncated render of a
            # real agency page - it must be a complete, different page.
            if len(response.body) > self.NOT_AN_AGENCY_PAGE_SIZE:
                return
            yield from self._retry(response, "no agency name found")
            return

        item = Feature()
        item["ref"] = response.url.rsplit("/", 1)[-1].removeprefix("assurance-")
        item["website"] = response.url
        # "Agence GMF AGEN" -> "Agen". "GMF" is already covered by
        # item_attributes["brand"], and the source name is all caps.
        branch = name.replace("\xa0", " ")
        branch = re.sub(r"\bAgence\b|\bGMF\b", "", branch, flags=re.I)
        item["branch"] = re.sub(r"\s+", " ", branch).strip().title()
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["city"] = (response.xpath('//*[@itemprop="addressLocality"]/text()').get() or "").title() or None
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/@content').get()

        # The only phone number ever present is a generic national call
        # centre line ("09 70 80 98 09" / tel:0970809809), identical on
        # every single agency page checked (Wayback and live) - not
        # agency-specific data, so deliberately not exposed as item["phone"].

        oh = self.parse_opening_hours(response)
        item["opening_hours"] = oh

        if not all([item.get("lat"), item.get("lon"), oh.as_opening_hours()]):
            yield from self._retry(response, "missing geometry or opening hours")
            return

        yield item

    def _retry(self, response: TextResponse, reason: str):
        if response.request is not None:
            if retry := get_retry_request(
                response.request,
                spider=self,
                max_retry_times=5,
                reason=reason,
                priority_adjust=random.randint(-20, -1),
            ):
                retry.meta["dont_cache"] = True
                yield retry

    @staticmethod
    def parse_opening_hours(response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        # Some agency pages carry a *second* "weekly-schedule" list further
        # down for a financial advisor sharing the same address ("Horaires
        # du conseiller financier"), with its own, unrelated hours - only
        # the first list (preceded by the "Horaires de l'agence" heading)
        # reflects the agency's own opening hours, so this is deliberately
        # scoped to the first "ul.weekly-schedule" on the page, not all of
        # them.
        schedule = response.css("ul.weekly-schedule")[:1]
        for day_row in schedule.css("li"):
            day_fr = day_row.css(".weekly-schedule-day::text").get()
            if not day_fr:
                continue
            day = sanitise_day(day_fr, DAYS_FR)
            if not day:
                continue
            ranges = [r.strip() for r in day_row.css(".weekly-schedule-range::text").getall()]
            if any("ferm" in r.lower() for r in ranges):
                oh.set_closed(day)
                continue
            for time_range in ranges:
                if "-" not in time_range:
                    continue
                open_time, close_time = (t.strip().replace("H", ":") for t in time_range.split("-", 1))
                oh.add_range(day, open_time, close_time)
        return oh
