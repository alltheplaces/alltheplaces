from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingJPSpider(Spider):
    name = "burger_king_jp"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.burgerking.co.jp/burgerking/BKJ0302.json",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
            body="message=%7B%22header%22%3A%7B%22result%22%3Atrue%2C%22error_code%22%3A%22%22%2C%22error_text%22%3A%22%22%2C%22info_text%22%3A%22%22%2C%22message_version%22%3A%22%22%2C%22login_session_id%22%3A%22%22%2C%22trcode%22%3A%22BKJ0302%22%2C%22cdCallChnn%22%3A%2202%22%7D%2C%22body%22%3A%7B%22tpSearchStore%22%3A%2203%22%2C%22searchKeyword%22%3A%22%22%2C%22storeServiceCode%22%3A%5B%22%22%5D%2C%22sort%22%3A%2202%22%2C%22xCoordinates%22%3A%22%22%2C%22yCoordinates%22%3A%22%22%2C%22page%22%3A1%2C%22dataCount%22%3A300%7D%7D",
            callback=self.parse,
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["body"]["data"]:
            item = Feature()
            item["ref"] = location["storCd"]
            item["lat"] = location["storCoordY"]
            item["lon"] = location["storCoordX"]
            item["branch"] = location["storNm"]
            item["addr_full"] = location["storAddr"]
            item["website"] = "https://www.burgerking.co.jp/"
            apply_category(Categories.FAST_FOOD, item)
            yield item
