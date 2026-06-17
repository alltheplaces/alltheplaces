from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AdloSpider(CrawlSpider):
    name = "adlo"
    item_attributes = {"brand": "ADLO", "brand_wikidata": "Q116862985"}
    start_urls = [
        "https://www.adlo-securitydoors.com/contact.xhtml",
        "https://www.adlo.at/kontakte.xhtml",
        "https://www.adlo-sicherheitstueren.de/kontakte.xhtml",
        "https://www.adlo.ch/kontakte.xhtml",
    ]

    rules = (
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="place-store"]'),
            callback="parse_item",
        ),
    )

    def parse_item(self, response):
        item = Feature()
        if response.xpath('(//*[@class="title"]//h1)[2]/text()').get():
            item["name"] = (
                response.xpath('(//*[@class="title"]//h1)[2]/text()')
                .get()
                .replace("Authorized ", "")
                .replace("Contracted", "")
            )
        else:
            item["name"] = (
                response.xpath('(//*[@class="title"]//h1)[1]/text()')
                .get()
                .replace("Authorized ", "")
                .replace("Contracted", "")
            )
        item["street_address"] = response.xpath("//address/text()[1]").get()
        item["addr_full"] = merge_address_lines([item["street_address"], response.xpath("//address/text()[2]").get()])
        if lat_lon := response.xpath('//*[@class = "gps"]/text()[2]').get():
            item["lat"], item["lon"] = lat_lon.split(",")
        item["phone"] = response.xpath('//span[contains(@href, "tel:")]/text()').get()
        item["email"] = response.xpath('//span[contains(@href, "mailto")]/text()').get()
        item["website"] = item["ref"] = response.url
        yield item
