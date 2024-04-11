from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SuzukiFRSpider(SitemapSpider):
    name = "suzuki_fr"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}
    sitemap_urls = [
        "https://www.suzuki.fr/sitemap.xml",
    ]
    sitemap_rules = [("/show/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["name"] = response.xpath(r"//title/text()").get().replace("|", "-")
        item["street_address"] = clean_address(response.xpath(r'//*[@class = "uppercase"]/text()').get().strip())
        item["addr_full"] = (
            item["street_address"] + ", " + clean_address(response.xpath(r'//*[@class = "uppercase"]/text()[2]').get())
        )
        item["phone"] = response.xpath(r'//*[contains(@href,"tel:")]/text()').get().replace(".", "")
        item["ref"] = item["website"] = response.url
        yield item
