from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class KwikFitGBSpider(SitemapSpider, StructuredDataSpider):
    name = "kwik_fit_gb"
    item_attributes = {"brand": "Kwik Fit", "brand_wikidata": "Q958053"}
    sitemap_urls = ["https://www.kwik-fit.com/sitemap.xml"]
    sitemap_rules = [("/locate-a-centre/", "parse_sd")]
    wanted_types = ["AutomotiveBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)

        yield item
