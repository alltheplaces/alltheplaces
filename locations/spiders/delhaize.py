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
    wanted_types = ["LocalBusiness"]
    custom_settings = {"REDIRECT_ENABLED": False, "METAREFRESH_ENABLED": False}
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["website"] = item["website"].replace("http://", "https://").lower()

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

        if item.get("image") in {
            "http://magasins.delhaize.lu/image/mobilosoft-testing?apiPath=rehab/delhaize-lu/images/location/proxy&imageSize=h_500",
            "http://magasins.delhaize.lu/image/mobilosoft-testing?apiPath=rehab/delhaize-lu/images/location/shop-n-go&imageSize=h_500",
            "https://stores.delhaize.be/image/mobilosoft-testing?apiPath=rehab/delhaize-be/images/location/mobilosoft-testing%20%281%29&imageSize=h_500",
            "http://magasins.delhaize.lu/image/mobilosoft-testing?apiPath=rehab/delhaize-lu/images/location/mobilosoft-testing%20%284%29&imageSize=h_500",
            "https://stores.delhaize.be/image/mobilosoft-testing?apiPath=rehab/delhaize-be/images/location/Proxy%20photo%20ge%CC%81ne%CC%81rique%201674480128409&imageSize=h_500",
            "https://stores.delhaize.be/image/mobilosoft-testing?apiPath=rehab/delhaize-be/images/location/ShopGo%201674480562182&imageSize=h_500",
            "http://magasins.delhaize.lu/image/mobilosoft-testing?apiPath=rehab/delhaize-lu/images/location/index&imageSize=h_500",
        }:
            del item["image"]
        if item.get("email") in {
            "klantendienst@delhaize.be",
            "serviceclients@delhaize.be",
            "serviceclients@delhaize.lu",
        }:
            del item["email"]

        if "delhaize.be" in response.url:
            item["website"] = item["extras"]["website:fr"] = response.url
            item["extras"]["website:nl"] = response.xpath('//link[@rel="alternate"][@hreflang="nl"]/@href').get()
            if fb := response.xpath('//a[@class="fb-btn"][contains(@href, "facebook.com")]/@href').get():
                set_social_media(item, SocialMedia.FACEBOOK, fb)
        else:
            item["website"] = response.url
            if fb := response.xpath('//ul[@class="socials"]//a[contains(@href, "facebook.com")]/@href').get():
                set_social_media(item, SocialMedia.FACEBOOK, fb)

        yield item
