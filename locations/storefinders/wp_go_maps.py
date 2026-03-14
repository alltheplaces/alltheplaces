from base64 import b64encode
from json import dumps
from typing import Any, AsyncIterator, Iterable
from zlib import compress

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.dict_parser import DictParser
from locations.items import Feature


class WpGoMapsSpider(Spider):
    """
    A base spider for WP Go Maps (https://wordpress.org/plugins/wp-google-maps/
    and https://www.wpgmaps.com/).

    Supply `allowed_domains` as the domain containing the store finder page.
    In some rare circumstances where the WordPress API endpoint is in a custom
    path, specify an explicit `start_urls` to the path of
    `/wp-json/wpgmza/v1/features/`.

    This store finder allows multiple feature layers to be returned from the
    same API endpoint. Most store locator implementations will only have a
    single feature layer with identifier of "1". Only in circumstances where a
    different feature layer needs to be used should a value for the `map_id`
    attribute of this class be supplied. All valid `map_id` values can be
    found by typing `window.WPGMZA.maps.map(i => {return i.id})` into a
    Firefox JavaScript console on the store finder page to observe any
    identifiers returned other than the default of "1".

    If clean-up to extracted data is required, or additional data fields need
    to be extracted, override the `post_process_item` method.
    """

    allowed_domains: list[str] = []
    start_urls: list[str] = []
    map_id: int | None = None

    async def start(self) -> AsyncIterator[Request]:
        api_endpoint = None
        if len(self.start_urls) == 0 and len(self.allowed_domains) == 1:
            api_endpoint = f"https://{self.allowed_domains[0]}/wp-json/wpgmza/v1/features/"
        elif len(self.start_urls) == 1:
            api_endpoint = self.start_urls[0]
        else:
            raise ValueError(
                "Specify one domain name in the allowed_domains list attribute or one URL in the start_urls list attribute."
            )
            return
        if api_endpoint:
            if isinstance(self.map_id, int):
                encoded_params = self.encode_params({"filter": dumps({"map_id": self.map_id})})
                yield Request(url=f"{api_endpoint}{encoded_params}")
            else:
                yield Request(url=api_endpoint)

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        yield from self.parse_stores(response)

    def encode_params(self, params: dict) -> str:
        """
        Parameters to the API are a JSON dictionary which is DEFLATE
        compressed and then base64 encoded.

        For example, for a URL of:
        https://www.wpgmaps.com/wp-json/wpgmza/v1/marker-listing/base64[...]

        [...] is the base64 encoded and DEFLATE compressed JSON dictionary,
        which has the format of (example):
        {"phpClass":"WPGMZA\\MarkerListing\\BasicList","start":0,"length":10,
        "map_id":15}
        """
        data = compress(dumps(params).encode())
        path = b64encode(data).rstrip(b"=").decode()
        return f"base64{path}"

    def pre_process_marker(self, marker: dict) -> dict:
        if "<img" in marker["title"]:
            marker.pop("title")
        if "<img" in marker["address"]:
            marker.pop("address")
        return marker

    def post_process_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item

    def parse_stores(self, response: TextResponse) -> Iterable[Feature]:
        for marker in response.json()["markers"]:
            location = self.pre_process_marker(marker)
            item = DictParser.parse(location)
            yield from self.post_process_item(item, location)
