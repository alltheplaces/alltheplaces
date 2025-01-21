from scrapy.spiders import SitemapSpider

from locations.open_graph_spider import OpenGraphSpider
from locations.pipelines.extract_gb_postcode import extract_gb_postcode


class LoungesGBSpider(SitemapSpider, OpenGraphSpider):
    name = "lounges_gb"
    item_attributes = {"brand": "Lounges", "brand_wikidata": "Q114313933"}
    sitemap_urls = ["https://thelounges.co.uk/lounges-sitemap.xml"]
    wanted_types = ["article"]

    def post_process_item(self, item, response, **kwargs):
        item["name"] = item["name"].split(" - ")[0].strip()
        lounge_header = response.xpath('//section[@class="lounge-header"]')
        if postcode := extract_gb_postcode(lounge_header.get()):
            if postcode[0].isalpha():
                item["postcode"] = postcode
        yield item
