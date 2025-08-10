from enum import Enum

from scrapy import Request, Spider
from scrapy.downloadermiddlewares.httpcompression import HttpCompressionMiddleware
from scrapy.http import HtmlResponse, Response


# As a temporary transition to use of AntiBotDetectionMiddleware,
# assume that Zyte API is capable of bypassing all anti-bot
# methods. This list will need to be amended after testing of Zyte
# API ability to bypass various anti-bot methods. This list will
# need to be frequently updated depending on the effectiveness of
# Zyte API's ability to rapidly bypass new/revised anti-bot methods.
class AntiBotMethods(Enum):
    # Azure Web Applicatigon Firewall bot protection documentation:
    # https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/bot-protection-overview
    AZURE_WAF = {"name": "Azure WAF", "zyte_bypassable": True}

    # Cloudflare bot protection documentation:
    # https://developers.cloudflare.com/bots/
    CLOUDFLARE = {"name": "Cloudflare", "zyte_bypassable": True}

    # DataDome bot protection product brochure:
    # https://datadome.co/products/bot-protection/
    DATADOME = {"name": "DataDome", "zyte_bypassable": True}

    # HUMAN Bot Defender bot protection product brochure:
    # https://www.humansecurity.com/products/human-bot-defender
    HUMAN = {"name": "HUMAN", "zyte_bypassable": True}

    # Imperva bot protection product brochure:
    # https://www.imperva.com/products/bot-detection-mitigation/
    IMPERVA = {"name": "Imperva", "zyte_bypassable": True}

    # Qrator bot protection documentation:
    # https://docs.qrator.net/en/technologies/tracking-cookie.html
    QRATOR = {"name": "Qrator", "zyte_bypassable": True}


class AntiBotDetectionMiddleware:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request: Request, response: Response, spider: Spider):
        if response.headers.get("cf-mitigated"):
            self.add_anti_bot_method(AntiBotMethods.CLOUDFLARE, spider)

        if response.headers.get("x-datadome"):
            self.add_anti_bot_method(AntiBotMethods.DATADOME, spider)

        if server := response.headers.get("server"):
            server_utf8 = self.decode_http_header_value(server)
            if server_utf8.upper() == "QRATOR":
                self.add_anti_bot_method(AntiBotMethods.QRATOR, spider)
            if response.status == 403 and server_utf8.upper() == "MICROSOFT-AZURE-APPLICATION-GATEWAY/V2":
                self.add_anti_bot_method(AntiBotMethods.AZURE_WAF, spider)

        if cookies := response.headers.getlist("set-cookie"):
            for cookie in cookies:
                cookie_utf8 = self.decode_http_header_value(cookie)
                if cookie_utf8.startswith("visid_incap_") or cookie_utf8.startswith("incap_ses_"):
                    self.add_anti_bot_method(AntiBotMethods.IMPERVA, spider)

        if response.status == 403:
            # We may need to decompress the response body before it
            # can be parsed to detect anti-bot methods. This is
            # necessary because HttpErrorMiddleware is ordered
            # before HttpCompressionMiddleware per:
            # 1. https://docs.scrapy.org/en/latest/topics/settings.html#spider-middlewares-base
            # 2. https://docs.scrapy.org/en/latest/topics/settings.html#downloader-middlewares-base
            # It is probably not a good idea to reorder these
            # default middleware orders.
            httpcm = HttpCompressionMiddleware.from_crawler(spider.crawler)
            decompressed_response = httpcm.process_response(request, response, spider)
            html_response = HtmlResponse(decompressed_response.url, body=decompressed_response.body)
            if html_response.xpath('//meta[@name="description" and @content="px-captcha"]'):
                self.add_anti_bot_method(AntiBotMethods.HUMAN, spider)

        return response

    @staticmethod
    def decode_http_header_value(raw_header_value: bytes) -> str:
        # It's not quite so simple to decode HTTP header values.
        # The below approach is simple and will most likely work due
        # to the encoding of HTTP header values being expected to be
        # set by anti-bot systems. It is not expected that anti-bot
        # systems would use different encodings for different sites.
        return raw_header_value.decode("utf-8")

    @staticmethod
    def add_anti_bot_method(anti_bot_method: AntiBotMethods, spider: Spider):
        if not getattr(spider, "anti_bot_methods", None):
            setattr(spider, "anti_bot_methods", [])
        if anti_bot_method not in spider.anti_bot_methods:
            anti_bot_name = anti_bot_method.value["name"]
            spider.logger.info(
                f"{anti_bot_name} anti-bot protection has been detected when executing spider {spider.name}."
            )
            spider.anti_bot_methods.append(anti_bot_method)
