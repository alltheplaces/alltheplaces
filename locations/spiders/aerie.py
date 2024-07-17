from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider

# We have to parse city pages to ensure we only scrap Aerie locations


class AerieSpider(SitemapSpider, StructuredDataSpider):
    name = "aerie"
    item_attributes = {"brand": "Aerie", "brand_wikidata": "Q25351619"}
    sitemap_urls = ["https://storelocations.ae.com/sitemap.xml"]
    sitemap_rules = [(r"https://storelocations.ae.com/\w\w/[^/]+/[^/]+.html$", "parse")]
    wanted_types = ["ClothingStore"]

    def parse(self, response: Response, **kwargs):
        for link in response.xpath('//span[@class="LocationName-brand"][text()="Aerie Store"]/../../@href').getall():
            yield response.follow(link, self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Aerie Store ")

        yield item
