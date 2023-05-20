import re
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


def extract_email(item, sel: Selector):
    for link in sel.xpath(".//a[contains(@href, 'mailto')]/@href").getall():
        link = link.strip()
        if link.startswith("mailto:") and "@" in link:
            item["email"] = urlparse(link).path
            return


def extract_phone(item, sel: Selector):
    for link in sel.xpath(".//a[contains(@href, 'tel')]/@href").getall():
        link = link.strip()
        if link.startswith("tel:"):
            item["phone"] = urlparse(link).path
            return


def clean_twitter(url: str) -> str:
    return (
        url.strip()
        .replace("http:", "")
        .replace("https:", "")
        .replace("www.", "")
        .replace("twitter.com", "")
        .replace("twitter.co.uk", "")
        .strip("@/")
        .split("?", 1)[0]
    )


def extract_twitter(item: Feature, sel: Selector):
    if twitter := sel.xpath('//meta[@name="twitter:site"]/@content').get():
        if twitter := clean_twitter(twitter):
            item["twitter"] = twitter
            return
    for url in sel.xpath('.//a[contains(@href, "twitter.com")]/@href').getall():
        if twitter := clean_twitter(url):
            item["twitter"] = twitter
            return


def extract_facebook(item: Feature, sel: Selector):
    for fb in sel.xpath(
        './/a[contains(@href, "facebook.com")]'
        '[not(contains(@href, " "))]'
        '[not(contains(@href, "events"))]'
        '[not(contains(@href, "posts"))]'
        '[not(contains(@href, "sharer.php"))]'
        '[not(contains(@href, "share.php"))]/@href'
    ).getall():
        url = urlparse(fb)
        if "facebook.com" not in url.netloc:
            continue
        if url.path in [None, "/", ""]:
            continue
        elif url.path in ["/profile.php", "/group.php"]:
            # Just copy id/gid param eg https://www.facebook.com/profile.php?id=100057371322568
            query = parse_qs(url.query)
            clean_query = {}
            for k, v in query.items():
                if k in ["id", "gid"]:
                    clean_query[k] = v[0]
            url = url._replace(scheme="https", netloc="www.facebook.com", query=urlencode(clean_query), fragment="")
        else:
            # Just copy the path eg https://www.facebook.com/Ernstingsfamily/
            url = url._replace(scheme="https", netloc="www.facebook.com", query="", fragment="")
        item["facebook"] = url.geturl()
        return

    if fb := sel.xpath('.//div[@class="fb-customerchat"][@page_id]/@page_id').get():
        item["facebook"] = f"https://www.facebook.com/profile.php?id={fb}"
        return


def extract_instagram(item: Feature, response: Selector):
    for instagram in response.xpath('.//a[contains(@href, "instagram.com")]/@href').getall():
        url = urlparse(instagram)
        if "instagram.com" not in url.netloc:
            continue
        url = url._replace(scheme="https", netloc="www.instagram.com", query="", fragment="")
        item["extras"]["contact:instagram"] = url.geturl()
        return


def extract_image(item, response):
    if image := response.xpath('//meta[@name="twitter:image"]/@content').get():
        item["image"] = image.strip()
        return
    if image := response.xpath('//meta[@name="og:image"]/@content').get():
        item["image"] = image.strip()


def get_url(response) -> str:
    if canonical := response.xpath('//link[@rel="canonical"]/@href').get():
        return canonical
    return response.url


class StructuredDataSpider(Spider):
    dataset_attributes = {"source": "structured_data"}

    wanted_types = [
        "LocalBusiness",
        "ConvenienceStore",
        "Store",
        "Restaurant",
        "BankOrCreditUnion",
        "GroceryStore",
        "FastFoodRestaurant",
        "Hotel",
        "Place",
        "ClothingStore",
        "DepartmentStore",
        "HardwareStore",
        "AutomotiveBusiness",
        "BarOrPub",
        "SportingGoodsStore",
        "Dentist",
        "AutoRental",
        "HardwareStore",
    ]
    search_for_email = True
    search_for_phone = True
    search_for_twitter = True
    search_for_facebook = True
    search_for_instagram = False
    search_for_image = True
    json_parser = "json"
    time_format = "%H:%M"

    def parse_sd(self, response):  # noqa: C901
        MicrodataParser.convert_to_json_ld(response)
        for wanted_type in self.wanted_types:
            if ld_item := LinkedDataParser.find_linked_data(response, wanted_type, json_parser=self.json_parser):
                self.pre_process_data(ld_item)

                item = LinkedDataParser.parse_ld(ld_item, time_format=self.time_format)

                url = get_url(response)

                if item["ref"] is None:
                    item["ref"] = self.get_ref(url, response)

                if isinstance(item["website"], list):
                    item["website"] = item["website"][0]

                if not item["website"]:
                    item["website"] = url
                elif item["website"].startswith("www"):
                    item["website"] = "https://" + item["website"]
                elif item["website"].startswith("/"):
                    item["website"] = urljoin(response.url, item["website"])

                if self.search_for_email and item["email"] is None:
                    extract_email(item, response)

                if self.search_for_phone and item["phone"] is None:
                    extract_phone(item, response)

                if self.search_for_twitter and item.get("twitter") is None:
                    extract_twitter(item, response)

                if self.search_for_facebook and item.get("facebook") is None:
                    extract_facebook(item, response)

                if self.search_for_image and item.get("image") is None:
                    extract_image(item, response)

                if self.search_for_instagram and not item["extras"].get("instagram"):
                    extract_instagram(item, response)

                if item.get("image") and item["image"].startswith("/"):
                    item["image"] = urljoin(response.url, item["image"])

                yield from self.post_process_item(item, response, ld_item) or []

    def get_ref(self, url: str, response: Response) -> str:
        if hasattr(self, "rules"):  # Attempt to pull a match from CrawlSpider.rules
            for rule in getattr(self, "rules"):
                for allow in rule.link_extractor.allow_res:
                    if match := re.search(allow, url):
                        if len(match.groups()) > 0:
                            return match.group(1)
        elif hasattr(self, "sitemap_rules"):
            # Attempt to pull a match from SitemapSpider.sitemap_rules
            for rule in getattr(self, "sitemap_rules"):
                if match := re.search(rule[0], url):
                    if len(match.groups()) > 0:
                        return match.group(1)
        return url

    def parse(self, response, **kwargs):
        yield from self.parse_sd(response)

    def pre_process_data(self, ld_data, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item, response, ld_data, **kwargs):
        """Override with any post-processing on the item."""
        yield from self.inspect_item(item, response)

    def inspect_item(self, item, response):
        """Deprecated, please use post_process_item(self, item, response, ld_data):"""
        yield item
