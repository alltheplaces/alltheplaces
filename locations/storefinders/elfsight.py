from typing import AsyncIterator
from urllib.parse import unquote

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request, TextResponse

from locations.json_blob_spider import JSONBlobSpider


class ElfsightSpider(JSONBlobSpider):
    """
    An Elfsight storefinder can either be a cloud-hosted service with an API
    endpoint of one of the following:
    - https://shy.elfsight.com/p/boot/?callback=a&shop=(shop)&w=(api_key)
    - https://core.service.elfsight.com/p/boot/?w=(api_key)

    Or an Elfsight storefinder may embed data within a JavaScript object
    embedded in a self-hosted storefinder page where the JavaScript object is
    contained within a HTML script element which has a HTML attribute named
    "data-elfsight-google-maps-options".

    To use this spider in cloud-hosted mode, specify the 'host' attribute as
    either "core.service.elfsight.com" or "shy.elfsight.com". The 'api_key'
    attribute must also be specified. If the host is "shy.elfsight.com" then
    the 'shop' attribute must also be specified.

    To use this spider in self-hosted storefinder page mode, specify a single
    URL for the 'start_urls' list attribute for the storefinder page which
    contains embedded location data.
    """

    # detection_rules = [
    #     DetectionRequestRule(
    #         url=r"^https?:\/\/shy\.elfsight\.com/p/boot/?callback=.*&shop=(?P<shop>.*)&w=(?P<api_key>[\w-]+)$",
    #     ),
    #     DetectionRequestRule(
    #         url=r"^https?:\/\/core\.service\.elfsight\.com/p/boot/?w=(?P<api_key>[\w-]+)$",
    #     ),
    # }

    dataset_attributes: dict = {}
    start_urls: list[str] = []
    host: str | None = None
    shop: str | None = None
    api_key: str | None = None

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        if self.host is not None:
            self.dataset_attributes["source"] = "api"
            self.dataset_attributes["api"] = "elfsight.com"
            if self.api_key is None:
                raise ValueError("The 'api_key' attribute must be specified if the 'host' attribute is also specified.")
                return
            if self.host == "core.service.elfsight.com":
                yield JsonRequest(f"https://{self.host}/p/boot/?w={self.api_key}")
            elif self.host == "shy.elfsight.com":
                if self.shop is None:
                    raise ValueError(
                        "The 'shop' attribute must be specified if the 'host' attribute is specified to be 'shy.elfsight.com'."
                    )
                    return
                yield JsonRequest(f"https://{self.host}/p/boot/?callback=a&shop={self.shop}&w={self.api_key}")
            else:
                raise ValueError("The 'host' attribute must only be 'core.service.elfsight.com' or 'shy.elfsight.com'.")
                return
        else:
            if len(self.start_urls) != 1:
                raise ValueError("Specify one URL in the start_urls list attribute.")
                return
            yield Request(url=self.start_urls[0])

    def extract_json(self, response: TextResponse) -> list[dict]:
        if self.host == "core.service.elfsight.com" or self.host == "shy.elfsight.com":
            data = parse_js_object(response.text)
            return data["data"]["widgets"][self.api_key]["data"]["settings"]["markers"]
        else:
            return parse_js_object(unquote(response.xpath("//@data-elfsight-google-maps-options").get()))["markers"]

    def pre_process_data(self, feature: dict) -> None:
        if "infoTitle" in feature:
            feature["name"] = feature.pop("infoTitle")
        feature["addr"] = feature.pop("infoAddress")
        feature["phone"] = feature.pop("infoPhone")
        feature["email"] = feature.pop("infoEmail")
        if coordinates := feature.get("coordinates"):
            feature["lat"], feature["lon"] = str(coordinates).split(", ", 1)
