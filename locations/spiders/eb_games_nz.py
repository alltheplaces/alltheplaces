from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class EbGamesNZSpider(SitemapSpider, StructuredDataSpider):
    name = "eb_games_nz"
    item_attributes = {"brand": "EB Games", "brand_wikidata": "Q5322604"}
    sitemap_urls = ["https://www.ebgames.co.nz/sitemap-stores.xml"]
    sitemap_rules = [(r"/stores/store/(\d+)-[-\w]+$", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        extract_google_position(item, response)

        yield item
