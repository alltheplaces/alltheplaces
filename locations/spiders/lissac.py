import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LissacSpider(SitemapSpider, StructuredDataSpider):
    name = "lissac"
    item_attributes = {"brand": "Lissac", "brand_wikidata": "Q63102559"}
    sitemap_urls = ["https://opticien.lissac.fr/sitemap.xml"]
    sitemap_rules = [(r"/c\d+-[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = ld_data["@id"].rsplit("#store-", 1)[-1]
        name = item.pop("name")

        if "Audition" in name and "Opticien" not in name and "Optique" not in name:
            item["name"] = "Lissac Audition"
            apply_category(Categories.SHOP_HEARING_AIDS, item)
        else:
            item["name"] = "Lissac"
            apply_category(Categories.SHOP_OPTICIAN, item)

        # Names vary between "Lissac l'Opticien <branch>", "Opticien <branch> - Lissac",
        # "<branch> - Lunettes de vue, de soleil, lentilles" and similar.
        branch = re.sub(r" - Lunettes de vue.*$| – Centre Auditif.*$| et appareils( auditifs)?$", "", name)
        branch = re.sub(
            r"^(Royer )?Lissac( Chevillard)?( l'opticien| Opticien| Audition -)?( |$)", "", branch, flags=re.I
        )
        branch = re.sub(r"^(et l')?(Opticien|Audioprothésiste)?( ?(et|&) (l')?Audioprothésiste)? ", "", branch)
        branch = re.sub(r"^(Opticien|Audioprothésiste) ", "", branch)
        branch = re.sub(r" - Lissac( Audition)?| - \W.*$", "", branch)
        branch = re.sub(r"^Lissac ", "", branch)
        item["branch"] = branch or None

        # Head office address shared by nearly every location
        if item.get("email") == "contact@lissac.fr":
            item.pop("email")

        yield item
