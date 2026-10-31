from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ItsuGBSpider(SitemapSpider):
    name = "itsu_gb"
    item_attributes = {"brand": "itsu", "brand_wikidata": "Q6094914"}
    sitemap_urls = ["https://www.itsu.com/sitemap_pages.xml"]
    sitemap_rules = [(r"/location/[^/]+/[^/]+/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath('//h1[@class="title"]/text()').get()
        item["addr_full"] = merge_address_lines(response.xpath("//address[not(@class)]/text()").getall())
        extract_google_position(item, response)
        item["ref"] = item["website"] = response.url
        return item
