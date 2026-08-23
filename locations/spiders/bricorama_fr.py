import re

from scrapy.spiders import SitemapSpider

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
from locations.structured_data_spider import StructuredDataSpider

STORE_URL_RE = re.compile(r"^https://www\.bricorama\.fr/magasin/[\w\-]+/(\d+)$")


class BricoramaFRSpider(SitemapSpider, StructuredDataSpider, CamoufoxSpider):
    name = "bricorama_fr"
    item_attributes = {"brand": "Bricorama", "brand_wikidata": "Q2925146"}
    allowed_domains = ["www.bricorama.fr"]
    sitemap_urls = ["https://www.bricorama.fr/sitemap/Store-BR-fr-EUR"]
    sitemap_rules = [(r"^https:\/\/www\.bricorama\.fr\/magasin\/[\w\-]+\/\d+$", "parse_sd")]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    captcha_type = "cloudflare_turnstile"

    def post_process_item(self, item, response, ld_data, **kwargs):
        # A small number of sitemap URLs redirect elsewhere instead of
        # loading the store page: either to the generic "/magasins" store
        # locator (e.g. a delisted store ID), which still carries a stray
        # LocalBusiness JSON-LD block, or to a rebranded store on the
        # sibling Bricomarché site (same corporate group, shared JSON-LD
        # template). Only keep items that landed on a genuine store URL.
        match = STORE_URL_RE.match(response.url)
        if not match:
            return

        # The JSON-LD "@id" is the same generic store-locator URL for every
        # store, so LinkedDataParser's ref ends up non-unique. Use the
        # numeric store code from the URL instead.
        item["ref"] = match.group(1)

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
