import re
from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import FormRequest, TextResponse

from locations.items import Feature


class HemmakvallSESpider(Spider):
    name = "hemmakvall_se"
    item_attributes = {"brand": "Hemmakväll", "brand_wikidata": "Q10521791"}
    allowed_domains = ["www.hemmakvall.se"]
    start_urls = ["https://www.hemmakvall.se/hitta-butik/"]
    no_refs = True

    def parse(self, response: TextResponse, **kwargs) -> Iterable[Feature]:
        if url_key := re.search(
            r"ajaxurl\":\"([a-z\/:\.-]+)\",\"nonce\":\"(.+)\"};",
            response.xpath('//*[@id="pinmeto-ajax-search-js-extra"]//text()').get(),
        ):
            yield FormRequest(
                url=url_key.group(1),
                formdata={"action": "pinmeto_search_locations", "nonce": url_key.group(2)},
                callback=self.parse_details,
            )

    def parse_details(self, response):
        html_data = Selector(text=response.json()["data"])
        for data in html_data.xpath('//*[@class="row row-collapse align-center"]'):
            item = Feature()
            item["branch"] = data.xpath(".//h4/text()").get().removeprefix("Hemmakväll - ")
            text_data = data.xpath('.//*[@class="icon-box-text last-reset"]/p//text()').getall()
            item["addr_full"] = text_data[0]
            item["phone"] = text_data[1]
            item["email"] = text_data[2]
            yield item
