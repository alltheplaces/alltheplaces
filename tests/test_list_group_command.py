from locations.extensions.add_lineage import VALID_GROUPS, Lineage, spider_class_to_lineage


def test_spider_group_resolution_from_path():
    """Verify that spiders in subdirectories resolve to the correct group."""
    from locations.spiders.infrastructure.aurora_city_council_traffic_signals_us import (
        AuroraCityCouncilTrafficSignalsUSSpider,
    )

    assert spider_class_to_lineage(AuroraCityCouncilTrafficSignalsUSSpider).group == "infrastructure"


def test_spider_group_resolution_brands_default():
    """Verify that top-level spiders default to brands."""
    from locations.spiders.greggs_gb import GreggsGBSpider

    assert spider_class_to_lineage(GreggsGBSpider).group == "brands"


def test_spider_group_override_via_lineage():
    """Verify that the lineage class attribute overrides path-based resolution."""
    from locations.spiders.greggs_gb import GreggsGBSpider

    original = getattr(GreggsGBSpider, "lineage", None)
    try:
        GreggsGBSpider.lineage = Lineage.Infrastructure
        assert spider_class_to_lineage(GreggsGBSpider).group == "infrastructure"
    finally:
        if original is None:
            del GreggsGBSpider.lineage
        else:
            GreggsGBSpider.lineage = original


def test_all_groups_have_at_least_one_spider():
    """Verify every defined group has at least one spider in the codebase."""
    from locations.exporters.geojson import iter_spider_classes_in_modules

    groups_seen = set()
    for spider_class in iter_spider_classes_in_modules():
        lineage = spider_class_to_lineage(spider_class)
        groups_seen.add(lineage.group)

    for group in VALID_GROUPS:
        assert group in groups_seen, f"No spiders found for group {group!r}"
