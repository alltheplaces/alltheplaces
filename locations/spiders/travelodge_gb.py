import html

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TravelodgeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "travelodge_gb"
    item_attributes = {"brand": "Travelodge", "brand_wikidata": "Q9361374"}
    sitemap_urls = ["https://www.travelodge.co.uk/sitemap-general.xml"]
    sitemap_rules = [(r"https://www.travelodge.co.uk/hotels/(\d+)/[^/]+$", "parse")]
    wanted_types = ["Hotel"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = html.unescape(item.pop("name"))
        yield item
