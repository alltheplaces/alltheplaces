from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DistriktstandvardenSESpider(SitemapSpider, StructuredDataSpider):
    name = "distriktstandvarden_se"
    item_attributes = {"brand": "Distriktstandvården", "brand_wikidata": "Q10474535"}
    sitemap_urls = ["https://distriktstandvarden.se/dtv_clinic-sitemap.xml"]
