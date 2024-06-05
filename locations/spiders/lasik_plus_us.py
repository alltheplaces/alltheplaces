from scrapy.spiders import SitemapSpider

from locations.items import SocialMedia, get_social_media, set_social_media
from locations.structured_data_spider import StructuredDataSpider


class LasikPlusUSSpider(SitemapSpider, StructuredDataSpider):
    name = "lasik_plus_us"
    item_attributes = {"brand": "LasikPlus", "brand_wikidata": "Q126111242"}
    sitemap_urls = ["https://www.lasikplus.com/robots.txt"]
    sitemap_follow = ["lasik_location.xml"]
    sitemap_rules = [(r"/location/([^/]+-lasik-center)/$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url

        if get_social_media(item, SocialMedia.FACEBOOK) == "https://www.facebook.com/LasikPlus/":
            return  # SEO spam

        yelp, fb, *_ = get_social_media(item, SocialMedia.FACEBOOK).split(", ")
        set_social_media(item, SocialMedia.YELP, yelp)
        set_social_media(item, SocialMedia.FACEBOOK, fb)

        yield item
