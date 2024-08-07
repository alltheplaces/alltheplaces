from urllib.parse import unquote

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import SocialMedia, set_social_media
from locations.structured_data_spider import StructuredDataSpider


class GrandvisionSpider(CrawlSpider, StructuredDataSpider):
    name = "grandvision"
    BRANDS = {
        "pearle": ("Pearle", "Q2231148"),
        "apollo": ("Apollo-Optik", "Q618940"),
        "grandoptical": ("GrandOptical", "Q3113677"),
        "optica2000": ("Optica2000", "Q15812731"),
        "synoptik": ("Synoptik", "Q10687541"),
        "visionexpress": ("Vision Express", "Q7936150"),
    }
    start_urls = [
        "https://www.pearle.at/filialen-uebersicht",
        "https://www.pearle.be/nl_BE/locatie",
        "https://www.pearle.nl/locatie",
        "https://www.apollo.de/filialen-uebersicht",
        "https://www.grandoptical.com/opticien/tous-les-magasins",
        # "https://www.grandoptical.be/"    website not working, also BE locations are no longer part of GrandVision
        "https://www.grandoptical.nl/locatie",  # Pearle Studio NL locations now branded as GrandOptical
        "https://www.grandoptical.pt/lojas/por-todo-pais",
        "https://www.grandoptical.sk/predajne",
        "https://www.optica2000.com/grupo-tiendas",
        "https://www.synoptik.se/butiksoversikt",
        "https://www.synoptik.dk/butiksoversigt",
        "https://www.visionexpress.com/store-overview",
        "https://www.visionexpress.ie/store-overview",
    ]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www\.pearle\.at/filialen/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.pearle\.at/filialen/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.pearle\.be/nl_BE/opticien/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.pearle\.be/nl_BE/opticien/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.pearle\.nl/opticien/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.pearle\.nl/opticien/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.apollo\.de/filialen/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.apollo\.de/filialen/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.grandoptical\.(com|nl)/opticien/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.grandoptical\.(com|nl)/opticien/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.grandoptical\.pt/lojas/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.grandoptical\.pt/lojas/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(LinkExtractor(allow=r"https://www\.grandoptical\.sk/predajne/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.optica2000\.com/buscar-opticas/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.optica2000\.com/buscar-opticas/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.synoptik\.se/butiker/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.synoptik\.se/butiker/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.synoptik\.dk/butikker/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"https://www\.synoptik\.dk/butikker/[-\w]+/[-\w]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(allow=r"https://www\.visionexpress\.(com|ie)/opticians/[-\w]+$"),
        ),
        Rule(
            LinkExtractor(allow=r"https://www\.visionexpress\.(com|ie)/opticians/[-\w]+/[-\w]+$"), callback="parse_sd"
        ),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)

        item["twitter"] = None
        set_social_media(item, SocialMedia.FACEBOOK, response.xpath('//a[contains(@href, "facebook")]/@href').get(""))
        instagram_link = response.xpath('//a[contains(@href, "instagram")]/@href').get("")
        instagram_link = instagram_link.split("next=")[1] if "next=" in instagram_link else instagram_link
        set_social_media(
            item,
            SocialMedia.INSTAGRAM,
            unquote(instagram_link),
        )
        set_social_media(item, SocialMedia.TIKTOK, response.xpath('//a[contains(@href, "tiktok")]/@href').get(""))
        set_social_media(item, SocialMedia.YOUTUBE, response.xpath('//a[contains(@href, "youtube")]/@href').get(""))
        set_social_media(item, SocialMedia.LINKEDIN, response.xpath('//a[contains(@href, "linkedin")]/@href').get(""))

        brand = response.url.split(".")[1]
        if brand_details := self.BRANDS.get(brand):
            item["brand"], item["brand_wikidata"] = brand_details
        apply_category(Categories.SHOP_OPTICIAN, item)

        yield item
