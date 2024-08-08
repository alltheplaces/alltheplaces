from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoodlifeFitnessSpider(SitemapSpider, StructuredDataSpider):
    name = "goodlife_fitness"
    item_attributes = {"brand": "GoodLife Fitness", "brand_wikidata": "Q3110654"}
    allowed_domains = ["goodlifefitness.com"]
    sitemap_urls = ["https://www.goodlifefitness.com/sitemap.xml"]
    sitemap_rules = [(r"/clubs/club.", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data):
        item["lat"] = response.xpath("//@data-club-lat").get()
        item["lon"] = response.xpath("//@data-club-lng").get()

        yield item
