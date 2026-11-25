import random

from scrapy import Request
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
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
    # Kept low on purpose: if the page markup changes, every page fails the same way and a high
    # retry count only burns Zyte credits until the run times out.
    incomplete_render_retries = 2

    def _parse_sitemap(self, response):
        # requires_proxy alone isn't enough; needs Zyte's browserHtml to get past the anti-bot.
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {
                "browserHtml": True,
                "geolocation": "FR",
                "javascript": True,
            }
            yield request

    def retry_incomplete_render(self, response: TextResponse, reason: str) -> Request | None:
        if response.request is None:
            return None
        request = response.request
        # "retry_times" is shared with the 404 retries above; count render retries separately so
        # neither kind of failure eats into the other's budget.
        render_request = request.replace(meta={**request.meta, "retry_times": request.meta.get("render_retries", 0)})
        retry = get_retry_request(
            render_request,
            spider=self,
            max_retry_times=self.incomplete_render_retries,
            reason=reason,
            # Shuffles retries within the queue; with a fixed adjustment they all came back at once.
            priority_adjust=random.randint(-20, -1),
        )
        if retry is not None:
            retry.meta["render_retries"] = retry.meta["retry_times"]
            retry.meta["retry_times"] = request.meta.get("retry_times", 0)
        return retry

    def parse(self, response: TextResponse, **kwargs):
        # Zyte sometimes returns the page before the JSON-LD has loaded; retry instead of
        # losing the location.
        yielded = False
        for result in self.parse_sd(response):
            yielded = True
            yield result
        if not yielded:
            if retry := self.retry_incomplete_render(response, "no structured data extracted"):
                yield retry

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        # "@id" would otherwise become the ref; drop it so the URL slug is used and refs stay stable.
        ld_data.pop("@id", None)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        if item.get("lat") is None or item.get("lon") is None:
            # Same incomplete-render issue as in parse().
            if retry := self.retry_incomplete_render(response, "missing geo"):
                yield retry
                return
            # Retries exhausted: keep the location without coordinates rather than dropping it.

        if item.get("name"):
            item["branch"] = item.pop("name").removeprefix("Agence MAAF ")
        yield item
