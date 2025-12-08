from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RolldAUSpider(CrawlSpider):
    name = "rolld_au"
    item_attributes = {"brand": "Roll'd", "brand_wikidata": "Q113114631"}
    start_urls = ["https://rolld.com.au/location-sitemap/"]
    rules = [Rule(LinkExtractor(allow="/location/"), callback="parse")]

    def parse(self, response, **kwargs):
        item = Feature()

        item["ref"] = item["website"] = response.url.split("?")[0]

        item["name"] = response.xpath('//h1[@class="entry-title"]/text()').get()
        item["street_address"] = response.xpath('//div[@class="wpsl-location-address"]/span/text()').get()
        item["postcode"] = response.xpath('normalize-space(//span[@class="zip-code"]/text())').get()
        item["addr_full"] = merge_address_lines(
            response.xpath('//div[@class="wpsl-location-address"]/span/text()').getall()
        )
        item["phone"] = response.xpath('//div[@class="phone-number"]/text()').get()

        if "closed" in item["name"].lower():
            return
        try:
            extract_google_position(item, response)
        except:
            pass

        yield item
