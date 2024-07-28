import json

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NuffieldHealthGBSpider(SitemapSpider, StructuredDataSpider):
    name = "nuffield_health_gb"
    item_attributes = {"brand_wikidata": "Q7068711"}
    sitemap_urls = ["https://www.nuffieldhealth.com/robots.txt"]
    sitemap_follow = ["gyms"]
    sitemap_rules = [(r"/gyms/([^/]+)$", "parse")]
    wanted_types = ["ExerciseGym"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if response.url == "https://www.nuffieldhealth.com/gyms/247":
            return

        if coords := response.xpath('//div[@class="location__map"]/@data-markers').get():
            coords = json.loads(coords)[0]
            item["lat"] = coords["lat"]
            item["lon"] = coords["lon"]
        item["phone"] = response.xpath('//span[@class="location__telephone"]/span[@itemprop="telephone"]/text()').get()

        yield item
