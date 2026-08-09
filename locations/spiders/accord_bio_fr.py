import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class AccordBioFrSpider(SitemapSpider, StructuredDataSpider):
    name = "accord_bio_fr"
    item_attributes = {"brand": "Accord Bio", "brand_wikidata": "Q140930088"}
    allowed_domains = ["accord-bio.fr"]
    sitemap_urls = ["https://www.accord-bio.fr/robots.txt"]
    sitemap_rules = [
        (r"magasin-bio/[^/]+/[^/]+/", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "épicerie" in ld_data["description"] or "proximité" in ld_data["description"]:
            # Deduce the category from the keywords used
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)

        # All shops from this network are organic only
        item["extras"]["organic"] = "only"

        if item["name"].isupper():
            # Lower the upper case names
            item["name"] = item["name"].title()

        if item["phone"] is not None:
            # Format phone number with French prefix
            item["phone"] = re.sub(r"^(0|\+33 )", "+33", item["phone"].replace("%20", " "))

        # Look for a street name in the address
        streetSearch = re.search(
            r"([\w\s]*)((?:route|impasse|rue|boulevard|allée|avenue|place)[^,]*)",
            item["street_address"],
            flags=re.IGNORECASE,
        )
        if streetSearch is not None:
            item["housenumber"] = streetSearch[1].strip()
            item["street"] = streetSearch[2].strip()

        if item["email"] == "contact@accord-bio.fr":
            # Wrong email detected because none was given, let's remove it
            item["email"] = ""

        if item["facebook"] == "https://www.facebook.com/accordbio":
            # Wrong fb page detected because none was given, let's remove it
            item["facebook"] = ""

        # The delivery information is only given in the description
        apply_yes_no(Extras.DELIVERY, item, "livraison" in ld_data["description"])

        yield item
