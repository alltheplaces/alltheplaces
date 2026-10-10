import re

from scrapy import Request

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Dogtopia runs a WordPress multisite: every franchise gets its own subsite at
# /<slug>/, and each subsite carries a LocalBusiness JSON-LD record on its home
# page. The subsite slugs are listed in the root sitemap index, which points at
# per-subsite sitemaps. Those per-subsite sitemaps mostly return a WordPress
# error page, so only the slugs are taken from them and the subsite home page is
# requested directly. Retired franchises answer 410 and are dropped by scrapy.

SITEMAP_INDEX = "https://www.dogtopia.com/sitemap_index.xml"


class DogtopiaUSSpider(StructuredDataSpider):
    name = "dogtopia_us"
    item_attributes = {"brand": "Dogtopia", "brand_wikidata": "Q112037444"}
    allowed_domains = ["www.dogtopia.com"]
    start_urls = [SITEMAP_INDEX]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_email = False
    search_for_image = False

    def parse(self, response, **kwargs):
        slugs = set(re.findall(r"https://www\.dogtopia\.com/([^/]+)/[a-z_]+-sitemap\.xml", response.text))
        for slug in sorted(slugs):
            yield Request(url=f"https://www.dogtopia.com/{slug}/", callback=self.parse_sd)

    def pre_process_data(self, ld_data, **kwargs):
        # "image" is an empty string on every page.
        ld_data.pop("image", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        address = ld_data.get("address") or {}
        if (address.get("addressCountry") or "").strip() not in ["United States", "USA", "US"]:
            return

        item["ref"] = response.url.strip("/").rsplit("/", 1)[-1]
        item["branch"] = (item.pop("name", None) or "").removeprefix("Dogtopia of ")

        apply_category(Categories.ANIMAL_BOARDING, item)

        yield item
