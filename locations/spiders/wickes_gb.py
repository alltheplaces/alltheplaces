from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WickesGBSpider(SitemapSpider, StructuredDataSpider):
    name = "wickes_gb"
    item_attributes = {"brand": "Wickes", "brand_wikidata": "Q7998350"}
    sitemap_urls = ["https://www.wickes.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.wickes\.co\.uk\/store\/(\d+)$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        yield item
