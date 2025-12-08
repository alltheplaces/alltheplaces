from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BastideFRSpider(SitemapSpider):
    name = "bastide_fr"
    item_attributes = {"brand": "Bastide le confort médical", "brand_wikidata": "Q2887693"}
    allowed_domains = ["bastideleconfortmedical.com"]
    sitemap_urls = ["https://www.bastideleconfortmedical.com/Assets/Rbs/Seo/100190/fr_FR/Rbs_Store_Store.1.xml"]

    def parse(self, response, **kwargs):

        feature = LinkedDataParser.parse(response, "Organization")
        feature["website"] = response.url
        feature["ref"] = response.url
        feature["name"] = "Bastide"

        yield feature
