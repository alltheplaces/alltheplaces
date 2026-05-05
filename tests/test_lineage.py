import pytest

from locations.extensions.add_lineage import VALID_GROUPS, Lineage, lineage_for_group, spider_class_to_lineage
from locations.spiders.asda_gb import AsdaGBSpider
from locations.spiders.greggs_gb import GreggsGBSpider


def test_class_override():
    AsdaGBSpider.lineage = Lineage.Brands
    assert spider_class_to_lineage(AsdaGBSpider) == Lineage.Brands

    AsdaGBSpider.lineage = Lineage.Aggregators
    assert spider_class_to_lineage(AsdaGBSpider) == Lineage.Aggregators


def test_expected():
    assert spider_class_to_lineage(GreggsGBSpider) == Lineage.Brands


def test_lineage_group_names():
    assert Lineage.Brands.group == "brands"
    assert Lineage.Addresses.group == "addresses"
    assert Lineage.Aggregators.group == "aggregators"
    assert Lineage.Governments.group == "government"
    assert Lineage.Infrastructure.group == "infrastructure"
    assert Lineage.Unknown.group == "brands"


def test_valid_groups():
    assert VALID_GROUPS == {"brands", "addresses", "aggregators", "government", "infrastructure"}


def test_lineage_for_group():
    assert lineage_for_group("brands") == Lineage.Brands
    assert lineage_for_group("addresses") == Lineage.Addresses
    assert lineage_for_group("aggregators") == Lineage.Aggregators
    assert lineage_for_group("government") == Lineage.Governments
    assert lineage_for_group("infrastructure") == Lineage.Infrastructure


def test_lineage_for_group_invalid():
    with pytest.raises(ValueError, match="Unknown group"):
        lineage_for_group("invalid_group")
