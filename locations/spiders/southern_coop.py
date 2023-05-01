from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SouthernCoopSpider(SitemapSpider, StructuredDataSpider):
    name = "southern_coop"
    item_attributes = {"brand": "Southern Co-op", "brand_wikidata": "Q7569773"}
    sitemap_urls = ["https://stores.thesouthernco-operative.co.uk/sitemap.xml"]
    sitemap_rules = [(r".co\.uk\/[-\w]+\/[-\w]+\/[-\w]+\.html$", "parse_sd")]
