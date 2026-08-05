import random

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class MaafFRSpider(SitemapSpider, StructuredDataSpider):
    name = "maaf_fr"
    item_attributes = {"brand": "MAAF", "brand_wikidata": "Q3331028"}
    sitemap_urls = ["https://www.maaf.fr/fr/sitemap-agences.xml"]
    # Only flat "/fr/assurance-<slug>" URLs are individual agency pages -
    # this same sitemap also lists the 17 region pages and ~101 department
    # pages, which this pattern deliberately excludes (confirmed: filtering
    # this way yields the same 492 agencies as crawling all 17 region
    # pages' own listings, so the sitemap is not stale here).
    sitemap_rules = [(r"/fr/assurance-([\w-]+)$", "parse")]
    custom_settings = {
        # Anti-bot protection intermittently serves a decoy 404 instead of
        # the real page (~15-20% of requests in testing), even through
        # Zyte's browserHtml rendering. A retry almost always succeeds.
        # Same pattern as locations/spiders/exxon_mobil.py for its own
        # intermittent-block symptom, just a different status code.
        "RETRY_HTTP_CODES": [404],
        "RETRY_TIMES": 5,
        # A handful of stubborn URLs still failed all 5 retries in one
        # batch run, all within the same second - the retries for a given
        # URL were firing back-to-back with nothing else left in the queue
        # to interleave with, giving the anti-bot layer no real variation
        # between attempts. A per-request delay (randomised by Scrapy's
        # default RANDOMIZE_DOWNLOAD_DELAY) spaces consecutive attempts out
        # in time; see also the randomised retry priority below, which
        # spaces them out in queue order too.
        "DOWNLOAD_DELAY": 3,
    }

    def _parse_sitemap(self, response):
        # Plain Zyte proxying (requires_proxy) is not enough here: the
        # site's anti-bot protection returns a ban response even through
        # Zyte's automatic anti-ban handling. Forcing Zyte's headless
        # browser rendering (browserHtml) is required to get past the JS
        # challenge, same approach as locations/spiders/intermarche.py.
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {
                "browserHtml": True,
                "geolocation": "FR",
                "javascript": True,
            }
            yield request

    def parse(self, response: TextResponse, **kwargs):
        # Zyte's browserHtml occasionally returns the page before it has
        # fully rendered client-side - sometimes so early that even the
        # InsuranceAgency JSON-LD script hasn't loaded yet, which makes
        # parse_sd() yield nothing at all for an otherwise-200 response.
        # Retry rather than silently lose the location.
        yielded = False
        for result in self.parse_sd(response):
            yielded = True
            yield result
        if not yielded and response.request is not None:
            if retry := get_retry_request(
                response.request,
                spider=self,
                max_retry_times=5,
                reason="no structured data extracted",
                priority_adjust=random.randint(-20, -1),
            ):
                yield retry

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        if item.get("name"):
            item["branch"] = item.pop("name").removeprefix("Agence MAAF ")

        # MAAF nests "email" inside the JSON-LD "address" block, which
        # LinkedDataParser does not check (it only looks for "telephone" there).
        if not item.get("email"):
            if addr := LinkedDataParser.get_case_insensitive(ld_data, "address"):
                if isinstance(addr, list):
                    addr = addr[0]
                if isinstance(addr, dict):
                    item["email"] = LinkedDataParser.get_case_insensitive(addr, "email")

        # Coordinates are published as separate schema.org/Place microdata
        # elsewhere on the page, not inside the InsuranceAgency JSON-LD block.
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/@content').get()

        if not item["lat"] or not item["lon"]:
            # Same incomplete-render symptom as in parse(), but here the
            # JSON-LD did load, just not (yet) the geo widget further down
            # the page. Retry instead of yielding a location with no
            # coordinates.
            if response.request is not None:
                if retry := get_retry_request(
                    response.request,
                    spider=self,
                    max_retry_times=5,
                    reason="missing geo microdata",
                    priority_adjust=random.randint(-20, -1),
                ):
                    yield retry
            return

        # openingHours uses "09H00" instead of "09:00", which the framework's
        # default parser does not match (it requires a colon separator), so
        # it silently yields no hours. Normalise and reparse it here instead.
        if hours := LinkedDataParser.get_case_insensitive(ld_data, "openingHours"):
            if isinstance(hours, list):
                hours = " ".join(hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours.replace("H", ":"))

        yield item
