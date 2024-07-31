import scrapy

from locations.spiders.timpson_gb import TimpsonGBSpider


class JohnsonCleanersGBSpider(scrapy.spiders.SitemapSpider):
    name = "johnson_cleaners_gb"
    item_attributes = {"brand": "Johnson Cleaners", "brand_wikidata": "Q6268527"}
    sitemap_urls = ["https://www.johnsoncleaners.com/sitemap.xml"]
    sitemap_rules = [("/branch/", "parse")]

    def parse(self, response):
        # Johnson Cleaners is owned by Timpson, they share a common back-end
        return TimpsonGBSpider.extract(response)
