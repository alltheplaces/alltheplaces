from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider

# Storelocator on https://www.coastalcountry.com/about/store-locations
# Individual pages have structured data


class CoastalCountrySpider(SitemapSpider, StructuredDataSpider):
    name = "coastal_country"
    item_attributes = {"brand": "Coastal"}
    allowed_domains = ["www.coastalcountry.com"]
    sitemap_urls = ["https://www.coastalcountry.com/sitemap.xml"]
    sitemap_rules = [(r"/store-locations/[\w-]+$", "parse_sd")]
