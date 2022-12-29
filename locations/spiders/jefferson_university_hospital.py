import scrapy
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.user_agents import BROSWER_DEFAULT


class JeffersonUniversityHospitalSpider(SitemapSpider):
    name = "jefferson_univ_hosp"
    item_attributes = {
        "brand": "Jefferson University Hospital",
        "brand_wikidata": "Q59676202",
    }
    allowed_domains = ["jeffersonhealth.org"]
    sitemap_urls = ["https://www.jeffersonhealth.org/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+$", "parse")]
    user_agent = BROSWER_DEFAULT

    def _parse_sitemap(self, response):
        for row in super()._parse_sitemap(response):
            yield scrapy.Request(url=f"{row.url}.model.json", callback=self.parse)

    def parse(self, response):
        item = DictParser.parse(response.json().get("locationLinkingData"))
        item["ref"] = item["website"]

        yield item
