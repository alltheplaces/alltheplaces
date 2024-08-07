from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class ZingPopCultureAUSpider(SitemapSpider, StructuredDataSpider):
    name = "zing_pop_culture_au"
    item_attributes = {"brand": "Zing Pop Culture Australia", "brand_wikidata": "Q23023711"}
    sitemap_urls = ["https://www.zingpopculture.com.au/sitemap-stores.xml"]
    sitemap_rules = [(r"/stores/store/(\d+)-[-\w]+$", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        extract_google_position(item, response)

        yield item
