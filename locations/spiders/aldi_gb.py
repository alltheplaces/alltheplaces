from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AldiGB(SitemapSpider, StructuredDataSpider):
    name = "aldi_ie_gb"
    item_attributes = {"brand": "Aldi", "brand_wikidata": "Q41171672", "country": "GB"}
    allowed_domains = ["aldi.co.uk", "aldi.ie"]
    download_delay = 10
    sitemap_urls = [
        "https://www.aldi.co.uk/sitemap/store-en_gb-gbp",
        "https://www.aldi.ie/sitemap/store-en_ie-eur",
    ]
    sitemap_rules = [("", "parse_sd")]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }
    wanted_types = ["GroceryStore"]
