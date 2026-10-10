from urllib.parse import urlparse

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class DekraAutomotiveFRSpider(SitemapSpider, StructuredDataSpider):
    name = "dekra_automotive_fr"
    BRANDS = {
        "DEKRA": {"brand": "DEKRA", "brand_wikidata": "Q383711"},
        "NORISKO": {"brand": "Norisko", "brand_wikidata": "Q141159455"},
        "AUTOCONTROL": {"brand": "Autocontrol", "brand_wikidata": "Q141252622"},
    }
    sitemap_urls = ["https://www.dekra-norisko.fr/sitemap.xml"]
    sitemap_rules = [(r"/(dekra|norisko|autocontrol)/controle-technique/", "parse_sd")]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = urlparse(response.url).query
        # "Centre contrôle technique NORISKO Arleux 59151" -> Norisko, branch "Arleux"
        enseigne, _, branch = item.pop("name").removeprefix("Centre contrôle technique ").partition(" ")
        item.update(self.BRANDS[enseigne])
        item["branch"] = branch.removesuffix(item["postcode"] or "").strip()
        apply_category(Categories.VEHICLE_INSPECTION, item)
        yield item
