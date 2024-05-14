from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SafeliteSpider(SitemapSpider, StructuredDataSpider):
    name = "safelite"
    item_attributes = {"brand": "Safelite", "brand_wikidata": "Q28797369"}
    sitemap_urls = ["https://www.safelite.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/", "parse_sd")]
    wanted_types = ["AutoGlass", "AutoRepair", "Service"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath('.//div[@class="store-map"]/@data-start-lat').extract_first()
        item["lon"] = response.xpath('.//div[@class="store-map"]/@data-start-lon').extract_first()
        yield item
