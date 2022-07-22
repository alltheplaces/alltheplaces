import json

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class GreeneKingInnsSpider(SitemapSpider):
    name = "greene_king_inns"
    item_attributes = {
        "brand": "Greene King Inns",
        "brand_wikidata": "Q5564162",
        "country": "GB",
    }
    sitemap_urls = ["https://www.greenekinginns.co.uk/sitemap.xml"]
    sitemap_rules = [
        (r"https:\/\/www\.greenekinginns\.co\.uk\/hotels\/([-\w]+)\/$", "parse")
    ]

    def parse(self, response):
        ld = response.xpath('//script[@type="application/ld+json"]//text()').get()
        if not ld:
            return
        ld_obj = json.loads(ld.replace("\n", ""))
        item = LinkedDataParser.parse_ld(ld_obj)
        item["website"] = response.url
        item["ref"] = response.url
        yield item
