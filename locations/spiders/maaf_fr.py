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
    # Sitemap also lists region/department pages; this keeps only individual agency pages.
    sitemap_rules = [(r"/fr/assurance-([\w-]+)$", "parse")]
    custom_settings = {
        # Anti-bot occasionally serves a decoy 404; a retry almost always succeeds.
        "RETRY_HTTP_CODES": [404],
        "RETRY_TIMES": 5,
        # Spreads out retries so they don't all land back-to-back on the same URL.
        "DOWNLOAD_DELAY": 3,
    }

    def _parse_sitemap(self, response):
        # requires_proxy alone isn't enough; needs Zyte's browserHtml to get past the anti-bot.
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {
                "browserHtml": True,
                "geolocation": "FR",
                "javascript": True,
            }
            yield request

    def parse(self, response: TextResponse, **kwargs):
        # Zyte sometimes returns the page before the JSON-LD has loaded; retry instead of
        # losing the location.
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

        # Email is nested inside "address"; LinkedDataParser only checks "telephone" there.
        if not item.get("email"):
            if addr := LinkedDataParser.get_case_insensitive(ld_data, "address"):
                if isinstance(addr, list):
                    addr = addr[0]
                if isinstance(addr, dict):
                    item["email"] = LinkedDataParser.get_case_insensitive(addr, "email")

        # Coordinates are separate schema.org/Place microdata, not in the JSON-LD.
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/@content').get()

        if not item["lat"] or not item["lon"]:
            # Same incomplete-render issue as in parse(); retry rather than yield no coordinates.
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

        # Source uses "09H00" instead of "09:00", which the default parser doesn't match.
        if hours := LinkedDataParser.get_case_insensitive(ld_data, "openingHours"):
            if isinstance(hours, list):
                hours = " ".join(hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours.replace("H", ":"))

        yield item
