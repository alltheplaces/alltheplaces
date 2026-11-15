from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LitrimarcheFRSpider(SitemapSpider, StructuredDataSpider):
    name = "litrimarche_fr"
    item_attributes = {"brand": "Litrimarché", "brand_wikidata": "Q127446387"}
    sitemap_urls = ["https://www.litrimarche.fr/lm_magasin-sitemap.xml"]
    sitemap_rules = [(r"/magasin/[^/]+/$", "parse_sd")]
    wanted_types = ["FurnitureStore"]
    name_is_branch = True
    # Store pages without their own JSON-LD sameAs would get the brand's footer link.
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item["branch"].removeprefix("Litrimarché ")
        # Stores without a photo fall back to the brand logo.
        if "logo-litrimarche" in item["image"]:
            item["image"] = None
        yield item
