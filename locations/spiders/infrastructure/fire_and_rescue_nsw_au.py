from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class FireAndRescueNswAUSpider(CrawlSpider):
    name = "fire_and_rescue_nsw_au"
    item_attributes = {"operator": "Fire and Rescue NSW", "operator_wikidata": "Q5451532"}
    allowed_domains = ["www.fire.nsw.gov.au"]
    start_urls = ["https://www.fire.nsw.gov.au/contact/contact-details/locations/station-index"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.fire\.nsw\.gov\.au\/contact\/fire-station\/\d{3}$"), callback="parse"
        )
    ]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "name": response.xpath("//main//h1/text()").get().strip(),
            "addr_full": response.xpath(
                '//main/div[2]//div[@class="card-panel white"][1]/p[contains(text(), "Address:")]/text()'
            )
            .get()
            .replace("Address:", "")
            .strip(),
            "state": "NSW",
            "phone": response.xpath(
                '//main/div[2]//div[@class="card-panel white"][1]/p[contains(text(), "Phone:")]/a/@href'
            )
            .get()
            .replace("tel:", ""),
            "website": response.url,
            "facebook": response.xpath(
                '//main/div[2]//div[@class="card-panel white"][1]/p[contains(text(), "Social media:")]/a/@href'
            ).get(),
        }
        extract_google_position(properties, response)
        apply_category(Categories.FIRE_STATION, properties)
        yield Feature(**properties)
