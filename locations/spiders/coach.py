from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import add_social_media
from locations.structured_data_spider import StructuredDataSpider


class CoachSpider(CrawlSpider, StructuredDataSpider):
    name = "coach"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    start_urls = [
        "https://de.coach.com/stores/index.html",
        "https://es.coach.com/stores/index.html",
        "https://fr.coach.com/stores/index.html",
        "https://it.coach.com/stores/index.html",
        "https://uk.coach.com/stores/index.html",
    ]
    rules = [
        Rule(LinkExtractor(allow=r"/stores/[-\w]+\.html$")),
        Rule(LinkExtractor(allow=r"/stores/[-\w]+/[-\w]+\.html$")),
        Rule(LinkExtractor(allow=r"/stores/[-\w]+/[-\w]+/[-\w]+\.html$"), callback="parse_sd"),
    ]
    wanted_types = ["Organization"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not ld_data.get("address", {}).get("streetAddress"):
            return  # skip bad duplicate linked data

        if wa := response.xpath('//a[contains(@href, "https://wa.me/")]/@href').get():
            add_social_media(item, "whatsapp", wa)

        item["website"] = response.url

        yield item
