from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AldiSudAUSpider(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_au"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672"}
    sitemap_urls = ["https://store.aldi.com.au/sitemap.xml"]
    sitemap_rules = [
        (r"https:\/\/store\.aldi\.com\.au\/\w+\/[-\w]+\/[-\w]+", "parse_sd")
    ]
