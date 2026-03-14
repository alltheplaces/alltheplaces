from typing import Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from scrapy.spiders.sitemap import iterloc, logger
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class KfcPHSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_ph"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["stores.kfc.com.ph"]
    sitemap_urls = ["https://stores.kfc.com.ph/robots.txt"]
    sitemap_rules = [(r"-fast-food-restaurant-.+-\d+\/Map$", "parse_sd")]
    wanted_types = ["Restaurant"]
    time_format = "%I:%M %p"

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        if response.url.endswith("/robots.txt"):
            for url in sitemap_urls_from_robots(response.text, base_url=response.url):
                if url.endswith("locations.xml"):
                    yield Request(url, callback=self._parse_sitemap)
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                logger.warning(
                    "Ignoring invalid sitemap: %(response)s",
                    {"response": response},
                    extra={"spider": self},
                )
                return

            s = Sitemap(body)
            it = self.sitemap_filter(s)

            if s.type == "sitemapindex":
                for loc in iterloc(it, self.sitemap_alternate_links):
                    if any(x.search(loc) for x in self._follow):
                        yield Request(loc, callback=self._parse_sitemap)
            elif s.type == "urlset":
                for loc in iterloc(it, self.sitemap_alternate_links):
                    for r, c in self._cbs:
                        if r.search(loc):
                            yield Request(loc, callback=c)
                            break
