import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.spiders.tesco_gb import set_located_in
from locations.spiders.walgreens import WalgreensSpider


class LabCorpUSSpider(SitemapSpider):
    name = "lab_corp_us"
    item_attributes = {"brand": "LabCorp", "brand_wikidata": "Q6466630"}
    sitemap_urls = ["https://locations.labcorp.com/robots.txt"]
    sitemap_rules = [(r"/\w\w/[^/]+/(\d+)/", "parse")]

    def parse(self, response: Response, **kwargs):
        # Remove comments from JSON
        json_blob = ""
        for line in (
            response.xpath('//script[@type="application/ld+json"][contains(text(), "MedicalBusiness")]/text()')
            .get()
            .splitlines()
        ):
            json_blob += line.split(" //", 1)[0]

        item = LinkedDataParser.parse_ld(json.loads(json_blob))
        if item.get("name", "").upper().endswith("WALGREENS"):
            set_located_in(WalgreensSpider.WALGREENS, item)
        item["name"] = None

        yield item
