from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class VitalantSpider(SitemapSpider):
    name = "vitalant"
    item_attributes = {"brand": "Vitalant", "brand_wikidata": "Q7887528"}
    sitemap_urls = ["https://www.vitalant.org/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]

    def parse(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//h1[@class="content__title"]/text()').get().replace("Vitalant", "")
        try:
            if address_data := response.xpath('//*[contains(@class,"location__address")]/p/text()').getall():
                address = address_data[0]
                line_2 = address_data[1]
                if line_2 is not None:
                    if "877" not in line_2:
                        address = address + line_2
                item["addr_full"] = clean_address(address)
        except:
            self.logger.warning(f"Could not parse hours: {address_data}")
        extract_google_position(item, response)
        yield item
