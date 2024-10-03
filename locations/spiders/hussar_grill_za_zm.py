from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, add_social_media
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import clean_facebook


class HussarGrillZAZMSpider(SitemapSpider):
    name = "hussar_grill_za_zm"
    item_attributes = {
        "brand": "The Hussar Grill",
        "brand_wikidata": "Q130232305",
    }
    sitemap_urls = ["https://www.hussargrill.co.za/robots.txt"]
    sitemap_rules = [
        (r"/find-us/[-\w]+/[-\w]+/$", "parse"),
    ]
    skip_auto_cc_domain = True

    def parse(self, response):
        item = Feature()
        if branch := response.xpath('.//div[contains(@class,"sub-title")]/h3/text()').get():
            item["branch"] = branch.strip()
        else:
            return  # Some dud locations in sitemap with no content
        item["website"] = response.url
        item["ref"] = response.url
        item["addr_full"] = clean_address(response.xpath('.//strong[contains(text(), "Address")]/../p/text()').getall())
        item["phone"] = response.xpath('.//a[contains(@href, "tel:")]/@href').get()
        # item["email"] = response.xpath('.//a[contains(@href, "mailto:")]/@href').get() # Email is protected

        extract_google_position(item, response)
        add_social_media(
            item, SocialMedia.TRIP_ADVISOR, response.xpath('.//a[contains(@href, "tripadvisor.co")]/@href').get()
        )
        add_social_media(
            item,
            SocialMedia.FACEBOOK,
            clean_facebook(
                response.xpath('.//div[@class="btn-primary-wrap"]/a[contains(@href, "facebook.com")]/@href').get()
            ),
        )

        item["opening_hours"] = OpeningHours()
        times = response.xpath('.//strong[contains(text(), "Trading Hours")]/../p/text()').getall()
        for day in times:
            item["opening_hours"].add_ranges_from_string(day)

        yield item
