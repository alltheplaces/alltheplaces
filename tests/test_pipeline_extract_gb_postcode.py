from locations.items import Feature
from locations.pipelines import ExtractGBPostcodePipeline


def test_extraction():
    item = Feature()
    item["country"] = "GB"
    item["addr_full"] = "Great Gutter Lane, Hull, hu10 6DP, United Kingdom"

    pl = ExtractGBPostcodePipeline()
    pl.process_item(item, None)

    assert item["postcode"] == "HU10 6DP"


def test_badformat_o():
    item = Feature()
    item["country"] = "GB"
    item["addr_full"] = "Eastfields Rd, Woodmansey, HU17 OXL, Beverley, United Kingdom"

    pl = ExtractGBPostcodePipeline()
    pl.process_item(item, None)

    assert item["postcode"] == "HU17 0XL"


def test_ie():
    item = Feature()
    item["country"] = "IE"
    item["addr_full"] = "7-9 Ennis Road Retail Park, Ennis Road, Limerick, V94 K240"

    pl = ExtractGBPostcodePipeline()
    pl.process_item(item, None)

    assert item["postcode"] == "V94 K240"
