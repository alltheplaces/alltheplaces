import pytest

from locations.country_utils import CountryUtils, get_locale


def test_country_fix():
    country_utils = CountryUtils()
    assert not country_utils.to_iso_alpha2_country_code(None)
    assert not country_utils.to_iso_alpha2_country_code("A")
    assert not country_utils.to_iso_alpha2_country_code("A1")
    assert "GB" == country_utils.to_iso_alpha2_country_code("GB")
    assert "GB" == country_utils.to_iso_alpha2_country_code("gb")
    assert "GB" == country_utils.to_iso_alpha2_country_code("Great Britain")
    assert "GB" == country_utils.to_iso_alpha2_country_code("United Kingdom")
    assert "GB" == country_utils.to_iso_alpha2_country_code("United Kingdom. ")
    assert "GB" == country_utils.to_iso_alpha2_country_code("GBR")
    assert "GB" == country_utils.to_iso_alpha2_country_code(" UK ")
    assert "MX" == country_utils.to_iso_alpha2_country_code("México")


def test_country_code_from_url():
    country_utils = CountryUtils()
    assert not country_utils.country_code_from_url(None)
    assert not country_utils.country_code_from_url([1, 2, 3])
    assert not country_utils.country_code_from_url("https://site.com/path")
    assert not country_utils.country_code_from_url("https://site.co.xx/path")
    assert not country_utils.country_code_from_url("https://site.co.gbr/path")
    assert "ES" == country_utils.country_code_from_url("https://site.co.es/path")
    assert "GB" == country_utils.country_code_from_url("https://site.co.uk/path")
    assert "GB" == country_utils.country_code_from_url("https://site.co.UK/path")


def test_country_code_from_spider_name():
    country_utils = CountryUtils()
    assert not country_utils.country_code_from_spider_name(None)
    assert not country_utils.country_code_from_spider_name([1, 2, 3])
    assert not country_utils.country_code_from_spider_name("fails")
    assert not country_utils.country_code_from_spider_name("fails_xx")
    assert not country_utils.country_code_from_spider_name("fails_gbr")
    assert "ES" == country_utils.country_code_from_spider_name("spider_es")
    assert "GB" == country_utils.country_code_from_spider_name("spider_UK")
    assert "GB" == country_utils.country_code_from_spider_name("spider_GB")
    assert "GB" == country_utils.country_code_from_spider_name("spider_with_more_words_GB")


def test_get_locale():
    assert get_locale("US") == "en-US"
    assert get_locale("GB") == "en-GB"
    assert get_locale("CN") == "zh-CN"
    assert not get_locale("")
    with pytest.raises(TypeError):
        get_locale(None)
