import logging

from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import Sitemap

from locations.items import Feature

logger = logging.getLogger(__name__)


class DominosPizzaINSpider(SitemapSpider):
    name = "dominos_pizza_in"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    sitemap_urls = ["https://www.dominos.co.in/store-locations/sitemap_store.xml"]

    def _parse_sitemap(self, response):
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
                        loc = loc.replace("store-locations", "store-location")
                        yield Request(loc, callback=self.parse)
                        break

    def parse(self, response):
        item = Feature()
        item["ref"] = response.url
        overview_tab = response.xpath('//div[@id="Overview-tab"]')
        columns = overview_tab.xpath('.//div[@class="mbot"]')
        for idx, column in enumerate(columns):
            if idx == 0:
                phone_path = column.xpath('.//div[not(@class="clear")]')[0]
                item["phone"] = phone_path.xpath(".//p/text()").extract_first()
            elif idx == 1:
                address_coord_path = column.xpath('.//div[not(@class="clear")]')[1]
                item["addr_full"] = address_coord_path.xpath(".//p/text()").extract_first()
                anchors = address_coord_path.xpath(".//a/@href").extract()
                for anchor in anchors:
                    if "google.com/maps" in anchor:
                        item["lat"], item["lon"] = anchor.split("destination=")[1].split(",")

        yield item


def iterloc(it, alt=False):
    for d in it:
        yield d["loc"]

        # Also consider alternate URLs (xhtml:link rel="alternate")
        if alt and "alternate" in d:
            yield from d["alternate"]
