import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class AccordBioFRSpider(SitemapSpider, StructuredDataSpider):
    name = "accord_bio_fr"
    allowed_domains = ["accord-bio.fr"]
    sitemap_urls = ["https://www.accord-bio.fr/robots.txt"]
    sitemap_rules = [(r"magasin-bio/[^/]+/[^/]+/", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        description = (ld_data.get("description") or "").casefold()
        if "épicerie" in description or "proximité" in description:
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
        street_match = re.search(
            r"(?P<housenumber>\d[\w\s-]*?)?\s*,?\s*(?P<street>(?:route|impasse|rue|boulevard|allée|avenue|place)\b[^,]*)",
            item["street_address"] or "",
            flags=re.IGNORECASE,
        )
        if street_match is not None:
            if street_match.group("housenumber") is not None:
                item["housenumber"] = street_match["housenumber"].strip()
            item["street"] = street_match["street"].strip()

        if item["email"] == "contact@accord-bio.fr":
            # Wrong email detected because none was given, let's remove it
            item.pop("email")

        if "facebook.com/accordbio" in item["facebook"]:
            # Wrong fb page detected because none was given, let's remove it
            item.pop("facebook")

        # The delivery information is only given in the description
        apply_yes_no(Extras.DELIVERY, item, "livraison" in description)

        yield item
