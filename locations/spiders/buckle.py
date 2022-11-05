import json

import scrapy

from locations.linked_data_parser import LinkedDataParser


class BuckleSpider(scrapy.spiders.SitemapSpider):
    name = "buckle"
    item_attributes = {
        "brand": "Buckle",
        "brand_wikidata": "Q4983306",
    }

    allowed_domains = ["local.buckle.com"]
    sitemap_urls = [
        "https://local.buckle.com/robots.txt",
    ]
    sitemap_rules = [(r"https://local\.buckle\.com/.*\d/", "parse")]

    def parse(self, response):
        # Buckle left a comment in the middle of the JSON LD in their
        # HTML, so we create a new one without it.
        lds = response.xpath('//script[@type="application/ld+json"]//text()').getall()
        for ld in lds:
            try:
                ld_obj = json.loads(ld, strict=False)
            except json.decoder.JSONDecodeError:
                ld_nocomments = (line.strip() for line in ld.split("\n"))
                ld = "".join(
                    line for line in ld_nocomments if not line.startswith("//")
                )
                script = response.selector.root.makeelement(
                    "script", {"type": "application/ld+json"}
                )
                script.text = ld
                response.selector.root.append(script)

        item = LinkedDataParser.parse(response, "ClothingStore")
        yield item
