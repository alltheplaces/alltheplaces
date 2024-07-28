import json

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


# Can't currently use StructuredDataSpider as there is no type in the source data
class AtiPhysicalTherapySpider(SitemapSpider):
    name = "ati_physical_therapy"
    item_attributes = {
        "brand": "ATI Physical Therapy",
        "brand_wikidata": "Q50039703",
        "country": "US",
    }
    allowed_domains = ["locations.atipt.com"]
    sitemap_urls = ["https://locations.atipt.com/sitemap.xml"]
    sitemap_rules = [(r"\.com\/([-\w]{3,})$", "parse")]

    def parse(self, response, **kwargs):
        if ld := response.xpath('//script[@type="application/ld+json"]//text()').get():
            item = LinkedDataParser.parse_ld(json.loads(ld))
            item["ref"] = response.url

            yield item
