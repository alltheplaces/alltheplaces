import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SallyBeautySpider(SitemapSpider, StructuredDataSpider):
    name = "sally_beauty"
    item_attributes = {
        "brand": "Sally Beauty",
        "brand_wikidata": "Q7405065",
    }
    sitemap_urls = ["https://stores.sallybeauty.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://stores.sallybeauty.com/[a-z]{2}/[a-z]+/beauty-supply-[\w-]+.html", "parse"),
    ]
    drop_attributes = {"name", "facebook"}
    search_for_twitter = False

    def parse(self, response, **kwargs):
        # Try to correct syntax errors
        for el in response.xpath('//script[@type="application/ld+json"]'):
            match = re.search(r',\s*"mainEntityOfPage"', el.root.text)
            el.root.text = el.root.text[: match.start()] + "}]"
        yield from self.parse_sd(response)
