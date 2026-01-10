from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.superdrug import SuperdrugSpider
from locations.spiders.tesco_gb import set_located_in
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import FIREFOX_LATEST


class ThePerfumeShopGBSpider(SitemapSpider, StructuredDataSpider):
    name = "the_perfume_shop_gb"
    item_attributes = {"brand": "The Perfume Shop", "brand_wikidata": "Q7756719"}
    sitemap_urls = ["https://www.theperfumeshop.com/robots.txt"]
    sitemap_rules = [("/store/", "parse")]
    custom_settings = {"USER_AGENT": FIREFOX_LATEST}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("The Perfume Shop ")
        item["street_address"] = clean_address(item["street_address"].replace("The Perfume Shop", ""))

        extract_google_position(item, response)

        if "superdrug" in response.url:
            set_located_in(SuperdrugSpider.item_attributes, item)

        yield item
