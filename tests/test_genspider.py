import argparse
import sys
from pathlib import Path
from types import ModuleType

import pytest
from locations.commands.genspider import Command


def test_add_options():
    parser = argparse.ArgumentParser(add_help=False)
    cmd = Command()
    cmd.settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
    cmd.parameters = {"brand": None, "brand_wikidata": None, "operator": None, "operator_wikidata": None}

    cmd.add_options(parser)
    dests = [a.dest for a in parser._actions]
    assert "brand_wikidata" in dests
    assert "operator_wikidata" in dests


@pytest.mark.parametrize(
    "wikidata, tags, expect_brand_wd, expect_operator_wd",
    [
        ("Q123", {"brand:wikidata": "Q123", "brand": "Foo Brand"}, "Q123", None),
        ("Q999", {"operator:wikidata": "Q999", "operator": "Bar Operator"}, None, "Q999"),
    ],
)
def test_auto_from_start_url_param(tmp_path, monkeypatch, wikidata, tags, expect_brand_wd, expect_operator_wd):
    monkeypatch.chdir(tmp_path)
    from locations.name_suggestion_index import NSI

    monkeypatch.setattr(NSI, "get_wikidata_code_from_url", lambda self, url: wikidata)
    monkeypatch.setattr(NSI, "iter_nsi", lambda self, code: iter([{"tags": tags}]))

    cmd = Command()
    cmd.settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
    cmd.parameters = {"brand": None, "brand_wikidata": None, "operator": None, "operator_wikidata": None}
    cmd.start_urls = ["https://example.com/path"]

    cmd.automatically_set_brand_or_operator_from_start_url()
    assert cmd.parameters["brand_wikidata"] == expect_brand_wd
    assert cmd.parameters["operator_wikidata"] == expect_operator_wd


def test_auto_from_start_url_no_match_does_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from locations.name_suggestion_index import NSI

    monkeypatch.setattr(NSI, "get_wikidata_code_from_url", lambda self, url: None)
    monkeypatch.setattr(NSI, "iter_nsi", lambda self, code: iter([]))

    cmd = Command()
    cmd.settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
    cmd.parameters = {"brand": None, "brand_wikidata": None, "operator": None, "operator_wikidata": None}
    cmd.start_urls = ["https://example.com/path"]

    cmd.automatically_set_brand_or_operator_from_start_url()
    assert cmd.parameters["brand_wikidata"] is None
    assert cmd.parameters["operator_wikidata"] is None


@pytest.mark.parametrize(
    "seed_key, wikidata, tags, gen_keys, expect_key, expect_class, expect_field, expect_value",
    [
        ("brand_wikidata", "Q123",
         {"brand:wikidata": "Q123", "brand": "Foo Brand", "name": "Fallback Brand"},
         ("foo_brand", "FooBrand"),
         "foo_brand", "FooBrand", "brand", "Foo Brand"),
        ("operator_wikidata", "Q777",
         {"operator:wikidata": "Q777", "operator": "Bar Operator", "name": "Fallback Operator"},
         ("bar_operator", "BarOperator"),
         "bar_operator", "BarOperator", "operator", "Bar Operator"),
    ],
)
def test_automatically_set_parameters_params(tmp_path, monkeypatch, seed_key, wikidata, tags, gen_keys, expect_key, expect_class, expect_field, expect_value):
    monkeypatch.chdir(tmp_path)
    from locations.name_suggestion_index import NSI

    monkeypatch.setattr(NSI, "iter_nsi", lambda self, code: iter([{"tags": tags}]))
    monkeypatch.setattr(NSI, "generate_keys_from_nsi_attributes", lambda attrs: gen_keys)

    cmd = Command()
    cmd.settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
    cmd.parameters = {"brand": None, "brand_wikidata": None, "operator": None, "operator_wikidata": None}
    cmd.parameters[seed_key] = wikidata

    cmd.automatically_set_parameters()
    assert cmd.parameters["spider_key"] == expect_key
    assert cmd.parameters["spider_class_name"] == expect_class
    assert cmd.parameters[expect_field] == expect_value


def test_automatically_set_parameters_multiple_matches_returns_early(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from locations.name_suggestion_index import NSI

    monkeypatch.setattr(
        NSI,
        "iter_nsi",
        lambda self, code: iter([
            {"tags": {"brand:wikidata": "Q123"}}, {"tags": {"brand:wikidata": "Q123"}}
        ]),
    )

    cmd = Command()
    cmd.settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
    cmd.parameters = {"brand": None, "brand_wikidata": "Q123", "operator": None, "operator_wikidata": None}

    cmd.automatically_set_parameters()
    assert "spider_key" not in cmd.parameters
    assert "spider_class_name" not in cmd.parameters
    assert cmd.parameters.get("brand") is None


def test_automatically_set_parameters_no_keys_generated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from locations.name_suggestion_index import NSI

    monkeypatch.setattr(
        NSI,
        "iter_nsi",
        lambda self, code: iter([{"tags": {"brand:wikidata": "Q1", "brand": "X"}}]),
    )
    monkeypatch.setattr(NSI, "generate_keys_from_nsi_attributes", lambda attrs: ())

    cmd = Command()
    cmd.settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
    cmd.parameters = {"brand": None, "brand_wikidata": "Q1", "operator": None, "operator_wikidata": None}

    cmd.automatically_set_parameters()
    assert "spider_key" not in cmd.parameters
    assert "spider_class_name" not in cmd.parameters
    assert cmd.parameters["brand"] == "X"


@pytest.mark.parametrize(
    "module,name,url,expected_domain,expected_classname",
    [
        ("foo_brand", "foo_brand", "https://foo.example.com/shops", "foo.example.com", "FooBrandSpider"),
        ("bar_operator", "bar_operator", "https://bar.example.org/x", "bar.example.org", "BarOperatorSpider"),
        ("acme", "acme", "http://acme.test", "acme.test", "AcmeSpider"),
    ],
)
def test_generate_template_variables_param(tmp_path, monkeypatch, module, name, url, expected_domain, expected_classname):
    monkeypatch.chdir(tmp_path)
    from locations.name_suggestion_index import NSI
    monkeypatch.setattr(NSI, "get_wikidata_code_from_url", lambda self, url: None)
    monkeypatch.setattr(NSI, "iter_nsi", lambda self, code: iter([]))

    cmd = Command()
    cmd.settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
    cmd.parameters = {"brand": "Foo Brand", "brand_wikidata": "Q123", "operator": None, "operator_wikidata": None}

    tvars = cmd._generate_template_variables(module, name, url, template_name="basic")

    assert tvars["project_name"] == "alltheplaces"
    assert isinstance(tvars["ProjectName"], str)
    assert tvars["module"] == module
    assert tvars["name"] == name
    assert tvars["url"] == url
    assert tvars["domain"] == expected_domain
    assert tvars["classname"] == expected_classname
    assert tvars["brand"] == "Foo Brand"
    assert tvars["brand_wikidata"] == "Q123"


@pytest.mark.parametrize("use_newspider_module", [False, True])
def test_genspider_param(tmp_path, monkeypatch, use_newspider_module):
    monkeypatch.chdir(tmp_path)

    from locations.commands import genspider as genspider_mod
    calls = []
    monkeypatch.setattr(
        genspider_mod,
        "render_templatefile",
        lambda path, **tvars: calls.append((str(path), tvars)),
    )

    from locations.name_suggestion_index import NSI
    monkeypatch.setattr(NSI, "get_wikidata_code_from_url", lambda self, url: None)
    monkeypatch.setattr(NSI, "iter_nsi", lambda self, code: iter([]))
    monkeypatch.setattr(NSI, "generate_keys_from_nsi_attributes", lambda attrs: ())

    template = tmp_path / "template.py"
    template.write_text("# TEMPLATE\n")

    if use_newspider_module:
        pkg = tmp_path / "spiderspkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("# dummy\n")
        modname = "dummy_spiders"
        fake_mod = ModuleType(modname)
        fake_mod.__file__ = str(pkg / "__init__.py")
        sys.modules[modname] = fake_mod
        settings = {"BOT_NAME": "alltheplaces", "NEWSPIDER_MODULE": modname, "LOG_LEVEL": "INFO"}
        expected_path = pkg / "foo_brand.py"
    else:
        settings = {"BOT_NAME": "alltheplaces", "LOG_LEVEL": "INFO"}
        expected_path = Path.cwd() / "foo_brand.py"

    cmd = Command()
    cmd.settings = settings
    cmd.parameters = {"brand": None, "brand_wikidata": None, "operator": None, "operator_wikidata": None}

    cmd._genspider(
        module="foo_brand",
        name="foo_brand",
        url="https://foo.example.com/",
        template_name="basic",
        template_file=str(template),
    )

    assert expected_path.exists()

    called_path = Path(calls[-1][0]).resolve()
    assert called_path == expected_path.resolve()

    assert calls[-1][1]["name"] == "foo_brand"
    assert calls[-1][1]["url"] == "https://foo.example.com/"
