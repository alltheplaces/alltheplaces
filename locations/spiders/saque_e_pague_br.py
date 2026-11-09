import re
from typing import Any, AsyncIterator, Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class SaqueEPagueBRSpider(JSONBlobSpider, PlaywrightSpider):
    name = "saque_e_pague_br"
    item_attributes = {"brand": "Saque e Pague"}
    # The store locator fetches its ATM list from a gist, whose URL changes from time to time.
    start_urls = ["https://www.saqueepague.com.br/encontre-um-ponto"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.start_urls[0], callback=self.parse_locator)

    def parse_locator(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(
            response.xpath('//script[contains(@src, "gist.githack.com")]/@src').get(), callback=self.parse_script
        )

    def parse_script(self, response: Response, **kwargs: Any) -> Any:
        yield Request(re.search(r'URL_JSON\s*=\s*"([^"]+)"', response.text).group(1))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["numero_logico"]
        item["located_in"] = item.pop("name").removesuffix(" - " + item["ref"]).strip()
        item["name"] = self.item_attributes["brand"]
        item["addr_full"] = feature["endereco"]
        item["city"] = feature["cidade"]
        item["state"] = feature["estado"]
        apply_category(Categories.ATM, item)
        yield item
