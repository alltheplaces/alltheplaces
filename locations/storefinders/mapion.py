import json
import re
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class MapionSpider(Spider):
    """
    Storefinder platform used by several Japanese chains' store locator
    pages, hosted on mapion.co.jp subdomains/paths or on the brand's domain.
    If the paginated list of stores ends with `attr/?t=attr_con&start=1`
    then it's a Mapion spider.

    There are two ways to collect the locations:

    1. JSON API (preferred). The map pages of the store finder call
       `https://lbs.mapion.co.jp/map/uc/PoiWithin?grp=...`. Set `api_group`
       to the value of the "grp" argument. The API returns every location
       in WGS 84 with a few requests. Optionally set `website_template`, a
       str.format() template taking the location id, for the detail page.

    2. Paginated listing pages. Set `feature_url_template` to a str.format()
       template for a listing page taking the page number. Listing pages
       stop once a page has no more detail links; detail pages embed the
       location's own data as a `window.infoJSON = {...};` blob. The
       coordinates on detail pages are usually in the Tokyo datum.

    Both ways pass the location's raw data to `pre_process_data` and
    `post_process_item`.
    """

    feature_url_template: str

    api_group: str | None = None
    api_page_size: int = 500  # the API errors on anything larger
    # The API refuses requests without a Referer from a Mapion hosted page.
    api_referer: str = "https://sasp.mapion.co.jp/"
    website_template: str | None = None
    additional_args: str = ""

    async def start(self) -> AsyncIterator[Request]:
        if self.api_group:
            yield self.make_api_request(1)
        else:
            yield Request(self.feature_url_template.format(1), meta={"page": 1}, callback=self.parse_list)

    def make_api_request(self, page: int) -> Request:
        # "start" is a page number, the bounding box covers all of Japan.
        return Request(
            f"https://lbs.mapion.co.jp/map/uc/PoiWithin?grp={self.api_group}&scl=1&crd=0&json=1&entref=1&dtm=wgs"
            f"&start={page}&pm={self.api_page_size}&nl=35&el=138&minnl=0&minel=0&maxnl=89&maxel=179&poi_status=1{self.additional_args}",
            headers={"Referer": self.api_referer},
            cb_kwargs={"page": page},
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, page: int) -> Iterable[Feature | Request]:
        # The JSON body is wrapped as "({...});"
        text = response.text.strip()
        data = json.loads(text[text.index("(") + 1 : text.rindex(")")])["mbml"]

        # if page * self.api_page_size <= int(data["Property"]["hit"]):
        if int(data["Property"]["end-index"]) < int(data["Property"]["hit"]):
            yield self.make_api_request(page + 1)

        pois = data["PoiList"].get("Poi", [])
        if isinstance(pois, dict):  # a page with a single location
            pois = [pois]
        for poi in pois:
            website = self.website_template.format(poi["id"]) if self.website_template else None
            yield from self.parse_location(poi, website, response)

    def parse_list(self, response: Response) -> Iterable[Request]:
        hrefs = set(response.xpath('//a[contains(@href, "/info/")]/@href').getall())
        if not hrefs:
            return

        for href in hrefs:
            yield response.follow(href, callback=self.parse_detail)

        page = response.meta["page"] + 1
        yield Request(self.feature_url_template.format(page), meta={"page": page}, callback=self.parse_list)

    def parse_detail(self, response: Response) -> Iterable[Feature]:
        if not (m := re.search(r"window\.infoJSON\s*=\s*(\{.*?\});", response.text)):
            return
        raw = re.sub(r'(?<!\\)((?:\\\\)*)\\(?!["\\/bfnrtu])', r"\1", m.group(1))  # some store pages have invalid JSON
        yield from self.parse_location(json.loads(raw), response.url, response)

    def parse_location(self, data: dict, website: str | None, response: Response) -> Iterable[Feature]:
        self.pre_process_data(data)

        item = DictParser.parse(data)
        item["extras"]["addr:province"] = data.get("kenname")
        if ruby := data.get("poi_name_yomi"):
            item["extras"]["branch:ja-Hira"] = ruby
        item["website"] = website
        yield from self.post_process_item(item, data, response) or []

    def pre_process_data(self, data: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
