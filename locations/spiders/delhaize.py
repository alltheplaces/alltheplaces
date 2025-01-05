from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, SocialMedia, set_social_media
from locations.structured_data_spider import StructuredDataSpider

AD_DELHAIZE = {"name": "AD Delhaize", "brand": "AD Delhaize", "brand_wikidata": "Q1184173"}
DELHAIZE = {"name": "Delhaize", "brand": "Delhaize", "brand_wikidata": "Q1184173"}
PROXY_DELHAIZE = {"name": "Proxy Delhaize", "brand": "Delhaize", "brand_wikidata": "Q1184173"}
SHOP_AND_GO = {"name": "Shop & Go", "brand": "Delhaize", "brand_wikidata": "Q1184173"}


class DelhaizeSpider(SitemapSpider, StructuredDataSpider):
    name = "delhaize"
    sitemap_urls = [
        "https://stores.delhaize.be/robots.txt",
        "https://magasins.delhaize.lu/robots.txt",
    ]
    sitemap_rules = [(r"/fr/([^/]+)$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["website"] = item["website"].replace("http://", "https://")

        if "/ad-delhaize-" in item["website"] or "/ad-" in item["website"]:
            item["branch"] = item.pop("name").removeprefix("AD ").removeprefix("Delhaize ")
            item.update(AD_DELHAIZE)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "/delhaize-" in item["website"] or "/sm-delhaize-" in item["website"]:
            item["branch"] = item.pop("name").removeprefix("SM ").removeprefix("Delhaize ")
            item.update(DELHAIZE)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "/proxy-delhaize-" in item["website"] or "/proxy-" in item["website"]:
            item["branch"] = item.pop("name").title().removeprefix("Proxy ").removeprefix("Delhaize ")
            item.update(PROXY_DELHAIZE)
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "/shop-and-go-" in item["website"] or "/shopandgo-" in item["website"] or "/shop-" in item["website"]:
            item["branch"] = (
                item.pop("name")
                .title()
                .removeprefix("Shop & Go ")
                .removeprefix("Shop&Go ")
                .removeprefix("Shop ")
                .removeprefix("Delhaize ")
            )
            item.update(SHOP_AND_GO)
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            self.logger.error("Unexpected shop type: {}".format(item["website"]))

        if "delhaize.be" in response.url:
            if fb := response.xpath('//a[@class="fb-btn"][contains(@href, "facebook.com")]/@href').get():
                set_social_media(item, SocialMedia.FACEBOOK, fb)
        else:
            if fb := response.xpath('//ul[@class="socials"]//a[contains(@href, "facebook.com")]/@href').get():
                set_social_media(item, SocialMedia.FACEBOOK, fb)

        yield item
