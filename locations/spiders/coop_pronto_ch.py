from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class CoopProntoCHSpider(SitemapSpider, StructuredDataSpider):
    name = "coop_pronto_ch"
    item_attributes = {
        "brand": "Coop Pronto",
        "brand_wikidata": "Q1129777",
    }
    sitemap_urls = ["https://www.coop-pronto.ch/sitemap.xml"]
    sitemap_follow = ["places"]
    sitemap_rules = [("/de/standorte/", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Skip LocalBusiness without geo (HQ info, not actual store)
        if not item.get("lat"):
            return

        item["branch"] = item.pop("name")
        item["ref"] = response.url.split("/")[-1]
        item["country"] = "CH"

        apply_category(Categories.SHOP_CONVENIENCE, item)

        page_text = response.text.lower()
        apply_yes_no(Extras.CAR_WASH, item, "waschanlage" in page_text)

        yield item
