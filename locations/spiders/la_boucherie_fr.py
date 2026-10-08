from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class LaBoucherieFRSpider(SitemapSpider, StructuredDataSpider):
    name = "la_boucherie_fr"
    item_attributes = {"brand": "La Boucherie", "brand_wikidata": "Q21427479"}
    sitemap_urls = ["https://www.la-boucherie.fr/nc_stores-sitemap.xml"]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = (
            item.pop("name", "")
            .removeprefix("La Boucherie, ")
            .removeprefix("votre ")
            .removeprefix("restaurant à viande ")
            .removeprefix("à ")
            .removeprefix("au ")
        )

        apply_category(Categories.RESTAURANT, item)
        yield item

    def iter_linked_data(self, response):
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if (
                isinstance(ld_obj, list) and ld_obj[0].get("@type") == "Restaurant"
            ):  # the restaurant item is always in a list
                yield ld_obj[0]
