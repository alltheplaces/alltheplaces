import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PapaJohnsIESpider(SitemapSpider):
    name = "papa_johns_ie"
    PAPA_JOHNS = {"brand": "Papa John's", "brand_wikidata": "Q2759586"}
    SUPERMACS = {"brand": "Supermac's", "brand_wikidata": "Q7643750"}
    item_attributes = PAPA_JOHNS
    sitemap_urls = ["https://papajohns.ie/store-sitemap.xml"]
    sitemap_rules = [(r"/store/.+", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//*[@class="split-title"]/text()').get()
        item["addr_full"] = merge_address_lines(response.xpath('//*[@class="sub-title"]/text()').getall())
        item["phone"] = response.xpath("//*[contains(text(),'Tel')]/text()").get()
        if map_url := response.xpath('//*[@class="store-front-image"]/@src').get():
            if coordinates := re.search(r"location=([-.\d]+),([-.\d]+)", map_url):
                item["lat"], item["lon"] = coordinates.groups()
        item["located_in"], item["located_in_wikidata"] = self.SUPERMACS.values()
        yield item
