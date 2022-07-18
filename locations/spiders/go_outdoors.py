from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from locations.google_url import url_to_coords
from locations.items import GeojsonPointItem
from locations.utils import find_linked_data


class GoOutdoorsSpider(CrawlSpider):
    name = "go_outdoors"
    item_attributes = {
        "brand": "Go Outdoors",
        "brand_wikidata": "Q75293941",
    }
    start_urls = ["https://www.gooutdoors.co.uk/stores"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"https:\/\/www\.gooutdoors\.co\.uk\/stores\/([-\w]+)$"
            ),
            callback="parse",
        )
    ]
    download_delay = 10

    def parse(self, response):
        store = find_linked_data(response, "LocalBusiness")
        # There is a better SportingGoodsStore ld object, but it requires JS to load

        if store:
            item = GeojsonPointItem()
            item.from_linked_data(store)

            item["name"] = "Go Outdoors"  # Yes, they have a typeo in their own name

            item["ref"] = response.url
            item["website"] = response.url
            item["country"] = "GB"  # UK isn't a valid county code

            item["lat"], item["lon"] = url_to_coords(store["hasmap"])

            yield item
