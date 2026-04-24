from scrapy.spiders import SitemapSpider

from locations.items import SocialMedia, set_social_media
from locations.structured_data_spider import StructuredDataSpider


class CoachSpider(SitemapSpider, StructuredDataSpider):
    name = "coach"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    sitemap_urls = [
        "https://de.coach.com/stores/sitemap.xml",
        "https://es.coach.com/stores/sitemap.xml",
        "https://fr.coach.com/stores/sitemap.xml",
        "https://it.coach.com/stores/sitemap.xml",
        "https://uk.coach.com/stores/sitemap.xml",
    ]
    sitemap_rules = [(r"/stores/[-\w]+/[-\w]+/[-\w]+\.html$", "parse_sd")]
    wanted_types = ["Organization"]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not ld_data.get("address", {}).get("streetAddress"):
            return  # skip bad duplicate linked data

        if wa := response.xpath('//a[contains(@href, "https://wa.me/")]/@href').get():
            set_social_media(item, SocialMedia.WHATSAPP, wa)

        item["website"] = response.url

        yield item
