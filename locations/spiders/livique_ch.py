import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class LiviqueCHSpider(SitemapSpider, StructuredDataSpider):
    name = "livique_ch"
    brands = {
        "Livique": "Q15851221",
        "Lumimart": "Q111722218",
        "Lumi": "Q111722218",
    }
    allowed_domains = ["www.livique.ch"]
    sitemap_urls = ["https://www.livique.ch/sitemap.xml"]
    sitemap_follow = ["/STORE-"]
    sitemap_rules = [(r"https://www\.[Ll]ivique\.ch/de/standorte/", "parse_sd")]
    wanted_types = ["Store"]
    search_for_phone = False
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True  # Data centre IP ranges appear to be blocked.

    def post_process_item(self, item, response, ld_data, **kwargs):
        for brand_name, brand_wikidata in self.brands.items():
            if brand_name in item["name"]:
                item["brand"] = brand_name
                item["brand_wikidata"] = brand_wikidata
                if "Lumi" in item["name"]:
                    apply_category(Categories.SHOP_LIGHTING, item)
                else:
                    apply_category(Categories.SHOP_FURNITURE, item)
                item["branch"] = item["name"].title().removeprefix(brand_name).strip()
                item.pop("name", None)
                break
        if not item.get("brand"):
            self.logger.error(
                "Could not parse brand from store title: {}. Perhaps this is a new brand?".format(item["name"])
            )

        item["country"] = "CH"
        item["image"] = self.cleanup_image(item["image"])
        if phone := item.get("phone"):
            item["phone"] = self.cleanup_phone(phone)
        item["ref"] = item["ref"].split("/")[-1].replace("_pos", "")
        item["street_address"] = self.cleanup_street(item["street_address"])
        item["website"] = item["website"].replace("_pos", "_POS")

        if hours_string := ", ".join(filter(None, ld_data.get("openingHours", []))):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_DE)

        yield item

    @staticmethod
    def cleanup_image(image):
        # Some stores have meaningless stock photos of sofas and lamps.
        return image if "POS" in image else None

    @staticmethod
    def cleanup_phone(phone):
        phone = "".join(phone.replace("Tel. 0", "+41").split())
        phone = phone.replace(".", "")
        return phone if re.match(r"^\+41\d{9}$", phone) else None

    @staticmethod
    def cleanup_street(street):
        return street.replace("\u00a0", " ")  # non-breaking space -> space
