import random

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GmfFRSpider(SitemapSpider, StructuredDataSpider):
    name = "gmf_fr"
    item_attributes = {"brand": "GMF", "brand_wikidata": "Q3095296"}
    # Every real agency page carries a single, self-contained JSON-LD
    # InsuranceAgency block (name/address/geo/openingHoursSpecification -
    # unlike the page's own HTML microdata, whose "geo" block is never
    # actually attached to its enclosing Organization item, see below).
    # "InsuranceAgency" is already in StructuredDataSpider's default
    # wanted_types, and the (unrelated, broken) microdata's "Organization"/
    # "Place" types are not, so convert_microdata's default conversion never
    # produces a competing/duplicate item here - no need to touch it.
    wanted_types = ["InsuranceAgency"]
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
        # one domain got a real crawl to 100% success - kept deliberately
        # conservative rather than pushed back up, since browserHtml
        # requests are already slow (~13-20s each observed) and there is no
        # throughput need to justify the risk of tripping the ban behaviour
        # again.
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    # Used in parse() to tell a genuine "not an agency page" apart from an
    # incomplete render, both of which make parse_sd() yield nothing. Real
    # agency pages' JSON-LD script sits at a near-constant ~9KB offset into
    # the document (agen: 8877, arras: 8879 - template/header content before
    # it, not anything agency-specific), and a full crawl of all 325 sitemap
    # agency URLs on 2026-08-05 found a clean gap in body sizes with no page
    # of any kind between ~10KB and ~70KB: every incomplete render was under
    # 10KB, every disambiguation page (see below) was over 75KB. 60KB sits
    # in that empty gap, comfortably past the JSON-LD's position and
    # comfortably short of the smallest disambiguation page found.
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
        yielded = False
        for result in self.parse_sd(response):
            yielded = True
            yield result
        if yielded:
            return

        # Two different things make parse_sd() yield nothing, and they need
        # opposite handling:
        #  1. A genuinely incomplete render (Zyte ban noise slipping through
        #     as a 200 with an empty/challenge body, the JSON-LD script
        #     itself never having loaded) - retry.
        #  2. A handful of "assurance-<slug>" URLs are not agency pages at
        #     all: for a city served by more than one GMF agency, the bare
        #     city-name slug (e.g. "assurance-paris", "assurance-lyon") is a
        #     search-results/disambiguation page listing every agency in
        #     that city (each already covered separately in the sitemap
        #     under its own suffixed slug, e.g. "paris-bastille"), not an
        #     agency record itself - confirmed these carry no InsuranceAgency
        #     JSON-LD at all (parse_sd() yields nothing on several checked
        #     directly). This is permanent - retrying gets the exact same
        #     listing page every time, wasting 5 attempts on something that
        #     will never become an agency record.
        # Both look identical from "nothing yielded" alone. The difference
        # is body size: a real agency page's own JSON-LD always sits at a
        # near-constant offset into the document (see NOT_AN_AGENCY_PAGE_SIZE),
        # so a response already well past that point with still nothing
        # extracted cannot be a truncated render of a real agency page - it
        # must be a complete, different page.
        if len(response.body) > self.NOT_AN_AGENCY_PAGE_SIZE:
            return
        if response.request is not None:
            if retry := get_retry_request(
                response.request,
                spider=self,
                max_retry_times=5,
                reason="no structured data extracted",
                priority_adjust=random.randint(-20, -1),
            ):
                retry.meta["dont_cache"] = True
                yield retry

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        # The JSON-LD "url" is an internal CMS link
        # (".../cms/render/live/fr/sites/gmf/contents/agences/agence-074"),
        # not the page itself - always override with the real page URL, and
        # derive "ref" from its slug rather than trust get_ref() on that URL.
        item["website"] = response.url
        item["ref"] = response.url.rsplit("/", 1)[-1].removeprefix("assurance-")

        # The JSON-LD "name" is the agency's own trading name (e.g. "ORLEANS
        # NORD"), already brand-free unlike MMA/MAAF's generic templated
        # name - just needs moving to "branch" (item_attributes["brand"]
        # already covers "GMF") and cleaning up the all-caps casing.
        if item.get("name"):
            item["branch"] = item.pop("name").title()

        # The only phone number ever present is a generic national call
        # centre line ("09 70 80 98 09" / tel:0970809809), identical on
        # every single agency page checked - not agency-specific data.
        item["phone"] = None

        # "GMF_Assurances" / facebook.com/GMFassurances - the same corporate
        # accounts found identically on every single agency page checked,
        # picked up by StructuredDataSpider's generic social link search -
        # not agency-specific, same treatment as MMA's generic Facebook page.
        item["twitter"] = None
        item["facebook"] = None

        # No explicit closed-day information is kept: GMF's own JSON-LD
        # openingHoursSpecification omits Sunday entirely and encodes a
        # closed Saturday as opens/closes "00:00" (which locations.hours's
        # add_range() silently drops rather than marking closed) - accepted
        # here rather than worked around with custom parsing, so
        # opening_hours only lists the days it actually has hours for.

        yield item
