from scrapy.spiders import SitemapSpider

from locations.spiders.tesco_gb import set_located_in
from locations.spiders.walgreens import WalgreensSpider
from locations.structured_data_spider import StructuredDataSpider


class LabCorpUSSpider(SitemapSpider, StructuredDataSpider):
    name = "lab_corp_us"
    item_attributes = {"brand": "LabCorp", "brand_wikidata": "Q6466630"}
    sitemap_urls = ["https://locations.labcorp.com/robots.txt"]
    sitemap_rules = [(r"/\w\w/[^/]+/(\d+)/", "parse_sd")]
    wanted_types = ["MedicalBusiness"]
    # Some ld+json blobs contain stray "//" comments, which json5 tolerates
    json_parser = "json5"

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("name", "").upper().endswith("WALGREENS"):
            set_located_in(WalgreensSpider.WALGREENS, item)
        item["name"] = None

        yield item
