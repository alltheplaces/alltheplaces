from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class ContempoZASpider(CrawlSpider):
    name = "contempo_za"
    item_attributes = {"brand": "Contempo", "brand_wikidata": "Q116619863"}
    allowed_domains = ["contemposhop.co.za"]
    start_urls = ["https://contemposhop.co.za/storelocator/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"\/storelocator\/[-\w]+\/$"),
            callback="parse",
        )
    ]

    def parse(self, response):
        oh = OpeningHours()
        oh.add_ranges_from_string(
            " ".join(response.xpath('.//tbody[@class="store-locator__regular-hours"]/tr/*/text()').getall())
        )
        properties = {
            "branch": response.xpath('.//div[@class="store-locator-view__name"]/text()').get().strip(),
            "phone": response.xpath('.//div[@class="store-locator-view__phone"]/text()').get().strip(),
            "addr_full": clean_address(response.xpath('.//div[@class="store-locator-view__address"]/text()').getall()),
            "lat": url_to_coords(response.xpath('.//div[@class="store-locator-view__directions"]/a/@href').get())[0],
            "lon": url_to_coords(response.xpath('.//div[@class="store-locator-view__directions"]/a/@href').get())[1],
            "opening_hours": oh,
            "website": response.request.url,
            "ref": response.request.url,
        }
        yield Feature(**properties)
