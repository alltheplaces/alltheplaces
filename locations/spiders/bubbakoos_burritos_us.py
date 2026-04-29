import chompjs
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BubbakoosBurritosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bubbakoos_burritos_us"
    item_attributes = {"brand": "Bubbakoo's Burritos", "brand_wikidata": "Q114619751"}
    sitemap_urls = ["https://locations.bubbakoos.com/sitemap.xml"]
    sitemap_rules = [(r"^https://locations\.bubbakoos\.com/locations/[a-z]{2}/[\w-]+$", "parse")]
    wanted_types = ["Restaurant"]

    def parse(self, response):
        for nextjs_script in response.xpath(
            "//script[starts-with(text(), 'self.__next_f.push([1,\"{\\\"@context')]/text()"
        ).getall():
            script_el = response.selector.root.makeelement("script", {"type": "application/ld+json"})
            script_el.text = chompjs.parse_js_object(nextjs_script)[1]
            response.selector.root.append(script_el)
        yield from super().parse(response)
