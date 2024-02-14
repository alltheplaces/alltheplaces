from scrapy.crawler import Crawler

from locations.items import Feature
from locations.pipelines.phone_clean_up import PhoneCleanUpPipeline
from locations.spiders.greggs_gb import GreggsGBSpider


def get_objects(phone, country):
    spider = GreggsGBSpider()
    spider.crawler = Crawler(GreggsGBSpider)
    spider.crawler._apply_settings()
    return (
        Feature(phone=phone, country=country),
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

    # Belgium
    item, pipeline, spider = get_objects("02/633.17.59", "BE")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "+32 2 633 17 59"

    for key in ["fax", "operator:phone", "operator:fax"]:
        assert pipeline.is_phone_key(key)
        item, pipeline, spider = get_objects(None, "TR")
        item["extras"] = {key: "+904441442"}
        pipeline.process_item(item, spider)
        assert item["extras"] == {key: "+90 4441442"}


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
    item["extras"]["fax"] = None
    pipeline.process_item(item, spider)
    assert item.get("phone") is None
    assert item.get("extras").get("fax") is None


def test_handle_none():
    item, pipeline, spider = get_objects(None, "US")
    pipeline.process_item(item, spider)
    assert item.get("phone") is None


def test_bad_data():
    item, pipeline, spider = get_objects(" ;    ", "CH")
    pipeline.process_item(item, spider)
    assert not item.get("phone")


def test_bad_seperator():
    item, pipeline, spider = get_objects("2484468015 / 2484468015", "US")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "+1 248-446-8015;+1 248-446-8015"

    item, pipeline, spider = get_objects("Fijo: 963034448 / Móvil: 604026467", "ES")
    pipeline.process_item(item, spider)
    assert item.get("phone") == "+34 963 03 44 48;+34 604 02 64 67"
