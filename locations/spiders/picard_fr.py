from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class PicardFRSpider(SitemapSpider):
    name = "picard_fr"
    item_attributes = {"brand": "Picard Surgelés", "brand_wikidata": "Q3382454"}

    allowed_domains = ["magasins.picard.fr"]
    sitemap_urls = ["https://magasins.picard.fr/sitemap.xml"]
    sitemap_follow = [r"https:\/\/magasins\.picard\.fr\/locationsitemap\d+\.xml"]

    def parse(self, response, **kwargs):

        feature = LinkedDataParser.parse(response, "LocalBusiness")
        feature["website"] = response.url
        feature["ref"] = response.url

        yield feature
