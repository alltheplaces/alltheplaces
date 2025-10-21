from typing import AsyncIterator, Iterable
from urllib.parse import unquote

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request, TextResponse

from locations.json_blob_spider import JSONBlobSpider


class ElfsightSpider(JSONBlobSpider):
    """
    An Elfsight spider will be one of:
    - https://shy.elfsight.com/p/boot/?callback=a&shop=(shop)&w=(api_key)
    - https://core.service.elfsight.com/p/boot/?w=(api_key)
    - Or embedded in data-elfsight-google-maps-options
    """

    # detection_rules = [
    #     DetectionRequestRule(
    #         url=r"^https?:\/\/shy\.elfsight\.com/p/boot/?callback=.*&shop=(?P<shop>.*)&w=(?P<api_key>[\w-]+)$",
    #     ),
    #     DetectionRequestRule(
    #         url=r"^https?:\/\/core\.service\.elfsight\.com/p/boot/?w=(?P<api_key>[\w-]+)$",
    #     ),
    # }

    host: str
    shop: str | None = None
    api_key: str

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        if self.host == "core.service.elfsight.com":
            yield JsonRequest(f"https://{self.host}/p/boot/?w={self.api_key}")
        elif self.host == "shy.elfsight.com":
            yield JsonRequest(f"https://{self.host}/p/boot/?callback=a&shop={self.shop}&w={self.api_key}")
        else:
            for url in self.start_urls:
                yield Request(url)

    def extract_json(self, response: TextResponse) -> list[dict]:
        if self.host == "core.service.elfsight.com" or self.host == "shy.elfsight.com":
            data = parse_js_object(response.text)
            return data["data"]["widgets"][self.api_key]["data"]["settings"]["markers"]
        else:
            return parse_js_object(unquote(response.xpath("//@data-elfsight-google-maps-options").get()))[
                "markers"
            ]

    def pre_process_data(self, feature: dict) -> None:
        if "infoTitle" in feature:
            feature["name"] = feature.pop("infoTitle")
        feature["addr"] = feature.pop("infoAddress")
        feature["phone"] = feature.pop("infoPhone")
        feature["email"] = feature.pop("infoEmail")
        if coordinates := feature.get("coordinates"):
            feature["lat"], feature["lon"] = str(coordinates).split(", ", 1)
