from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser


class GoOutdoorsSpider(CrawlSpider):
    name = "go_outdoors"
    item_attributes = {
        "brand": "Go Outdoors",
        "brand_wikidata": "Q75293941",
    }
    start_urls = ["https://www.gooutdoors.co.uk/stores"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https:\/\/www\.gooutdoors\.co\.uk\/stores\/([-\w]+)$"),
            callback="parse",
        )
    ]

    def parse(self, response):
        store = LinkedDataParser.find_linked_data(response, "LocalBusiness")
        # There is a better SportingGoodsStore ld object, but it requires JS to load

        if store:
            item = LinkedDataParser.parse_ld(store)

            item["name"] = "Go Outdoors"  # Yes, they have a typeo in their own name

            item["website"] = response.url
            item["country"] = "GB"  # UK isn't a valid county code

            yield item
