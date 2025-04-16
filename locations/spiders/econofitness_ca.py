from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class EconofitnessCASpider(CrawlSpider, StructuredDataSpider):
    name = "econofitness_ca"
    item_attributes = {"brand": "Éconofitness", "brand_wikidata": "Q123073582"}
    start_urls = ["https://econofitness.ca/en/results?searchmode=searchall&searchtext=&filters="]
    rules = [Rule(LinkExtractor(r"/en/gym/[-\w]+/\d+-"), callback="parse_sd")]
    wanted_types = ["ExerciseGym"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removesuffix(" 24/7")
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lon").get()
        yield item
