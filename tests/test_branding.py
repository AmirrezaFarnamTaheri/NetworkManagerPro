import json

import branding
import core
import broker_runtime
import enterprise_policy
import event_log
import hosts_manager
import nmp_cli


def test_branding_is_core_identity_source():
    identity = branding.product_identity()

    assert identity["name"] == core.APP_DISPLAY_NAME == "Lucid Net"
    assert identity["version"] == core.APP_VERSION
    assert identity["technical_app_id"] == core.APP_NAME == "LucidNet"
    assert identity["event_source"] == event_log.SOURCE == "LucidNet"
    assert identity["policy_registry_root"] == enterprise_policy.POLICY_ROOT
    assert identity["broker_pipe_name"] == broker_runtime.PIPE_NAME
    assert hosts_manager.MANAGED_BEGIN == "# LucidNet BEGIN"
    assert "Safe Windows network control" in identity["tagline"]
    assert "local-first" in identity["promise"]


def test_brand_architecture_preserves_reserved_names_and_safety_boundary():
    architecture = {item["name"]: item for item in branding.brand_architecture()}

    assert architecture["Lucid Net"]["status"] == "active"
    assert architecture["OmniRoute"]["status"] == "panel"
    assert architecture["Synapse"]["status"] == "panel"
    assert architecture["ForgeHub"]["status"] == "panel"
    assert architecture["AtlasFleet"]["status"] == "panel"
    assert architecture["PulseGuard"]["status"] == "panel"
    assert architecture["PhantomCore"]["status"] == "restricted"
    assert "Lucid" not in architecture
    assert "legal, ethical, safety, and feasibility review" in branding.SAFETY_BOUNDARY


def test_product_vision_contains_maturity_layers():
    vision = branding.product_vision()

    assert set(vision) == {"near_term", "mid_term", "long_term"}
    assert any("Context-aware profiles" in item for item in vision["mid_term"])
    assert any("Enterprise readiness" in item for item in vision["long_term"])


def test_cli_branding_commands_are_machine_readable(capsys):
    assert nmp_cli.run(["about", "--json"]) == 0
    about = json.loads(capsys.readouterr().out)
    assert about["identity"]["name"] == "Lucid Net"
    assert about["brand_architecture"]

    assert nmp_cli.run(["vision", "--json"]) == 0
    vision = json.loads(capsys.readouterr().out)
    assert "mid_term" in vision["vision"]

    assert nmp_cli.run(["brand", "--json"]) == 0
    brand = json.loads(capsys.readouterr().out)
    assert any(item["name"] == "Lucid Net" for item in brand["brand_architecture"])
    assert any(item["brand"] == "ForgeHub" for item in brand["panel_branding"])


def test_packaging_and_enterprise_files_match_branding_source():
    installer = open("installer/LucidNet.iss", "r", encoding="utf-8").read()
    build_script = open("scripts/build_release.ps1", "r", encoding="utf-8").read()
    spec = open("main.spec", "r", encoding="utf-8").read()
    admx = open("enterprise/LucidNet.admx", "r", encoding="utf-8").read()

    assert f'#define MyAppName "{branding.PRODUCT_NAME}"' in installer
    assert f'#define MyAppVersion "{branding.PRODUCT_VERSION}"' in installer
    assert f'#define MyAppPublisher "{branding.TECHNICAL_APP_ID}"' in installer
    assert f'#define MyAppExeName "{branding.INSTALLER_BASENAME}.exe"' in installer
    assert branding.INSTALLER_APP_ID in installer
    assert "branding.INSTALLER_BASENAME" in build_script
    assert "name=branding.INSTALLER_BASENAME" in spec
    assert branding.POLICY_REGISTRY_ROOT in admx


def test_license_is_agpl_3_only():
    pyproject = open("pyproject.toml", "r", encoding="utf-8").read()
    license_text = open("LICENSE", "r", encoding="utf-8").read()

    assert 'license = "AGPL-3.0-only"' in pyproject
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3" in license_text
