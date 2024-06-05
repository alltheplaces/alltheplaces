from scrapy.spiders import SitemapSpider

from locations.open_graph_parser import OpenGraphParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone


class FrancoMancaSpider(SitemapSpider):
    name = "franco_manca_gb"
    item_attributes = {"brand": "Franco Manca", "brand_wikidata": "Q28404417"}
    sitemap_urls = ["https://www.francomanca.co.uk/restaurant-sitemap.xml"]

    def parse(self, response, **kwargs):
        item = OpenGraphParser.parse(response)
        item["name"] = "Franco Manca"
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        extract_phone(item, response)
        item["addr_full"] = merge_address_lines(response.xpath('//p/a[@class="is-address"]/text()').getall())
        item["branch"] = response.xpath('//h1[@class="heading-xl"]/text()').get()
        yield item
