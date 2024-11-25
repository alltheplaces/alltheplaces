from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature, SocialMedia, set_social_media
from locations.structured_data_spider import StructuredDataSpider


class EggsUpGrillUSSpdier(SitemapSpider, StructuredDataSpider):
    name = "eggs_up_grill_us"
    item_attributes = {"brand": "Eggs Up Grill", "brand_wikidata": "Q131319129"}
    sitemap_urls = ["https://locations.eggsupgrill.com/robots.txt"]
    sitemap_rules = [(r"\.com/\w\w/[^/]+/(\d+)/$", "parse")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")

        set_social_media(
            item,
            SocialMedia.YELP,
            response.xpath('//a[@class="location-info__socials-icon"][contains(@href, "yelp.com")]/@href').get(),
        )
        set_social_media(
            item,
            SocialMedia.INSTAGRAM,
            response.xpath('//a[@class="location-info__socials-icon"][contains(@href, "instagram.com")]/@href').get(),
        )

        yield item
