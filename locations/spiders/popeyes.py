from chompjs import chompjs
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PopeyesSpider(SitemapSpider, StructuredDataSpider):
    name = "popeyes"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}
    sitemap_urls = ["https://locations.popeyes.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.popeyes.com/\w\w/.+/.+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if data := response.xpath('//script[@class="js-map-data"]/text()').get():
            if loc := chompjs.parse_js_object(data):
                item["lat"] = loc["latitude"]
                item["lon"] = loc["longitude"]

        yield item
