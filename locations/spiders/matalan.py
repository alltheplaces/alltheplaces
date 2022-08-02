from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class MatalanSpider(SitemapSpider):
    name = "matalan"
    item_attributes = {
        "brand": "Matalan",
        "brand_wikidata": "Q12061509",
    }
    sitemap_urls = [
        "https://www.matalan.co.uk/sitemap/stores.xml",
    ]
    sitemap_rules = [
        (
            r"https:\/\/www\.matalan\.co\.uk\/stores\/([-\w]+)$",
            "parse",
        )
    ]

    def parse(self, response):
        yield LinkedDataParser.parse(response, "DepartmentStore")
