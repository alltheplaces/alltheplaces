import csv
from _csv import Reader
from io import StringIO
from typing import AsyncIterator, Iterable
from urllib.parse import urlencode

from chompjs import parse_js_object
from scrapy import Request, Spider
from scrapy.http import Response

from locations.geo import country_iseadgg_centroids


class EMapSpider(Spider):
    """
    Zenrin e-map store locator. It returns POIs as EUC-JP JS files that assigns
    a csv string as `ZdcEmapHttpResult[1] = '...'`. `zdcemaphttp.cgi` proxies a radius query to the
    `nkyoten.cgi` seemingly listening to 127.0.0.1 backend and returns the result .

    Set `map_id` (and `host` when it differs from the default e-map host)
    """

    map_id: str
    host = "www.e-map.ne.jp"
    max_items = 1640
    radius_km = 24

    def request_url(self, params: dict) -> str:
        """Build the zdcemaphttp.cgi URL wrapping the nkyoten query for the given params."""
        target = urlencode({"target": f"http://127.0.0.1/cgi/nkyoten.cgi?{urlencode(params)}"})
        return f"https://{self.host}/p/{self.map_id}/zdcemaphttp.cgi?{target}&zdccnt=1&enc=EUC"

    def make_request(
        self,
        lat: float,
        lon: float,
        radius: float,
        offset: int = 1,
        count: int = 900,
        extra_params: dict | None = None,
        **cb_kwargs,
    ):
        """Build a radius search request centred on the given coordinates."""
        params = {
            "cid": self.map_id,
            "pos": offset,
            "cnt": count,
            "enc": "EUC",
            "lat": lat,
            "lon": lon,
            "knsu": self.max_items,
            "rad": radius,
            "hour": 1,
        }
        if extra_params:
            params.update(extra_params)
        return Request(
            self.request_url(params),
            cb_kwargs={"lat": lat, "lon": lon, "radius": radius, "offset": offset, "count": count, **cb_kwargs},
        )

    async def start(self) -> AsyncIterator[Request]:
        """Yield a grid of radius-search requests that covers Japan."""
        radius_m = self.radius_km * 1000
        for lat, lon in country_iseadgg_centroids("JP", self.radius_km):
            yield self.make_request(lat, lon, radius_m)

    def parse(self, response: Response, lat: float, lon: float, radius: float, offset: int, count: int = 900, **kwargs):
        """Decode the response, paginate past if any truncation, and pass each row to `parse_rows`."""
        reader, rec_count, hit_count = self.get_reader(response)
        if hit_count >= self.max_items:
            self.logger.warning("Maximum number of items returned in one query, consider lowering the radius")
        if rec_count >= hit_count:
            yield self.make_request(lat, lon, radius, offset + rec_count)
        yield from self.parse_rows(reader)

    def parse_rows(self, rows: Iterable[list[str]]):
        """Yield a Feature for each row; implemented by subclasses."""
        raise NotImplementedError

    def get_reader(self, response: Response) -> tuple[Reader, int, int]:
        """Decode an EUC-JP JS response into a TSV csv reader, returning it with rec_count and hit_count."""
        js_body = response.body.decode("euc-jp")
        # chompjs sees the array index as an array itself, so get just the string itself:
        js_str = js_body[js_body.find("'") : js_body.rfind("'") + 1]
        # For some reason, neither Python json nor chompjs like just the string on its own, so wrap it in an array
        js_ls = f"[{js_str}]"
        (tsv_str,) = parse_js_object(js_ls)
        reader = csv.reader(StringIO(tsv_str), delimiter="\t")
        _, rec_count, hit_count = map(int, next(reader))
        assert rec_count <= hit_count, (rec_count, hit_count)
        return reader, rec_count, hit_count
