from scrapy.crawler import Crawler

from locations.items import GeojsonPointItem
from locations.pipelines import PhoneCleanUpPipeline
from locations.spiders.greggs_gb import GreggsGBSpider


def get_objects(phone, country):
    spider = GreggsGBSpider()
    spider.crawler = Crawler(GreggsGBSpider)
    return (
        GeojsonPointItem(phone=phone, country=country),
        PhoneCleanUpPipeline(),
        spider,
    )


def test_handle():
    # Switzerland
    item, pipeline, spider = get_objects("0442017500", "CH")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "+41 44 201 75 00"

    # USA
    item, pipeline, spider = get_objects("(248) 446-8015", "US")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "+1 248-446-8015"


def test_handle_int():
    item, pipeline, spider = get_objects(2484468015, "US")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "+1 248-446-8015"


def test_handle_invalid():
    # 243 is not (yet) assigned in the North American Numbering Plan
    item, pipeline, spider = get_objects("2434577249", "US")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "2434577249"


def test_handle_missing():
    item, pipeline, spider = get_objects(None, "CH")
    pipeline.process_item(item, spider)
    assert item.get("phone") == None


def test_bad_data():
    item, pipeline, spider = get_objects("Fijo: 963034448 / Móvil: 604026467", "ES")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "Fijo: 963034448 / Móvil: 604026467"

    item, pipeline, spider = get_objects(" ;    ", "CH")
    pipeline.process_item(item, spider)
    assert not item.get("phone")
