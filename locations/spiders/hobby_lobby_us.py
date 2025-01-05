from urllib.parse import urlparse

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HobbyLobbyUSSpider(SitemapSpider, StructuredDataSpider):
    name = "hobby_lobby_us"
    allowed_domains = ["www.hobbylobby.com"]
    item_attributes = {
        "brand": "Hobby Lobby",
        "brand_wikidata": "Q5874938",
    }
    sitemap_urls = ["https://www.hobbylobby.com/sitemap-Store.xml"]
    sitemap_rules = [
        (r"/stores/search/(\d+)$", "parse_sd"),
    ]
    time_format = "%I:%M %p"
    # There are only social links for branch, not location
    search_for_twitter = False
    search_for_facebook = False

    def pre_process_data(self, ld_data, **kwargs):
        ld_data.pop("name", None)
        # Broken image link
        ld_data.pop("image", None)

        # ID/ref should be store number, not main website URL
        url = urlparse(ld_data["url"])
        ref = url.path.split("/")[-1]
        ld_data["@id"] = ref
        # Store URLs have the wrong domain
        url = url._replace(scheme="https", netloc="www.hobbylobby.com")
        ld_data["url"] = url.geturl()

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CRAFT, item)
        yield item
