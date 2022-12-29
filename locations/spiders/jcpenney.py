from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser
from locations.user_agents import BROSWER_DEFAULT


class JCPenneySpider(CrawlSpider):
    name = "jcpenney"
    item_attributes = {"brand": "JCPenney", "brand_wikidata": "Q920037"}
    allowed_domains = ["jcpenney.com"]
    start_urls = ["https://jcpenney.com/locations/"]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/[-\w]{2}$"), follow=True),
        Rule(LinkExtractor(allow=r"/locations/[-\w]{2}/[-\w]+/[-\w]+.html$"), follow=True, callback="parse"),
    ]
    user_agent = BROSWER_DEFAULT

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        if not (ld_item := LinkedDataParser.find_linked_data(response, "DepartmentStore")):
            return

        item = LinkedDataParser.parse_ld(ld_item)
        item["ref"] = item["website"] = response.url
        yield item
