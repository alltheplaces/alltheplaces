import re

from scrapy.spiders import SitemapSpider

from locations.open_graph_spider import OpenGraphSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_email, extract_facebook, extract_instagram


class LoungesGBSpider(SitemapSpider, OpenGraphSpider):
    name = "lounges_gb"
    item_attributes = {"brand": "Lounges", "brand_wikidata": "Q114313933"}
    sitemap_urls = ["https://thelounges.co.uk/lounges-sitemap.xml"]
    wanted_types = ["article"]

    def post_process_item(self, item, response, **kwargs):
        item["name"] = item["name"].split(" - ")[0].strip()

        lounge_header = merge_address_lines(response.xpath('//section[@class="lounge-header"]/p//text()').getall())
        if m := re.match(r"(.+)(?: •|,) ([\d ]+) •", lounge_header):
            item["addr_full"], item["phone"] = m.groups()

        extract_email(item, response)
        extract_facebook(item, response)
        extract_instagram(item, response)

        yield item
