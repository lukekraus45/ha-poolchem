"""Tests for household-configured product label rules."""

from pypoolchem.dosing.chemicals import ChemicalType
import pytest

from custom_components.poolchem.product_profiles import (
    label_fixed_dose,
    label_linear_dose,
    label_table_dose,
    load_product_profiles,
    parse_product_profiles,
)

SPAGUARD_PROFILE = {
    "acid": {
        "product_name": "SpaGuard pH Decreaser",
        "method": "label_table",
        "minimum_total_alkalinity": 125,
        "per_gallons": 200,
        "unit": "tsp",
        "round_to": 0.25,
        "wait_minutes": 30,
        "dose_table": [
            {"ph_min": 7.6, "ph_max": 7.8, "amount": 0.5},
            {"ph_min": 7.8, "ph_max": 8.0, "amount": 0.75},
            {"ph_min": 8.0, "ph_max": 8.4, "amount": 1.5},
            {"ph_min": 8.4, "ph_max": 14.0, "amount": 2.0},
        ],
    },
    "alkalinity": {
        "product_name": "SpaGuard Total Alkalinity Increaser",
        "method": "label_linear",
        "amount": 3,
        "per_gallons": 100,
        "raises_ppm": 25,
        "unit": "tsp",
        "round_to": 0.25,
    },
    "shock": {
        "product_name": "SpaGuard Enhanced Shock",
        "method": "label_fixed",
        "amount": 3,
        "per_gallons": 500,
        "unit": "tbsp",
        "wait_minutes": 30,
        "round_to": 0.25,
    },
}


def test_parse_spaguard_product_profiles() -> None:
    """A household can configure label schedules as structured JSON."""
    parsed = parse_product_profiles(SPAGUARD_PROFILE)
    assert parsed["acid"]["product_name"] == "SpaGuard pH Decreaser"


def test_builtin_spaguard_preset_has_three_label_rules() -> None:
    profiles = load_product_profiles("spaguard_spa", "{}")
    assert set(profiles) == {"acid", "alkalinity", "shock"}
    assert profiles["acid"]["strength_percent"] == 93.2
    assert profiles["shock"]["strength_percent"] == 58.2


def test_reject_invalid_product_profile_json() -> None:
    with pytest.raises(ValueError, match="valid JSON"):
        parse_product_profiles("not-json")
    with pytest.raises(ValueError, match="requires product_name"):
        parse_product_profiles({"acid": {"method": "label_fixed"}})
    with pytest.raises(ValueError, match="incompatible"):
        parse_product_profiles(
            {
                "alkalinity": {
                    "product_name": "Wrong product",
                    "chemical_type": "dry_acid",
                    "method": "label_linear",
                    "amount": 1,
                    "per_gallons": 100,
                    "raises_ppm": 25,
                }
            }
        )


def test_spaguard_ph_decreaser_scales_bottle_table_for_335_gallons() -> None:
    """pH 8.4 uses the printed 1.5 tsp / 200 gal bracket at TA 240."""
    result = label_table_dose(
        SPAGUARD_PROFILE["acid"],
        current_ph=8.4,
        total_alkalinity=240,
        volume_gallons=335,
        chemical_type=ChemicalType.DRY_ACID,
    )
    assert result is not None
    assert result.amount == 2.5
    assert result.unit == "tsp"
    assert result.chemical.name == "SpaGuard pH Decreaser"
    assert "30 minutes" in result.notes


def test_ph_label_profile_requires_label_ta_minimum() -> None:
    result = label_table_dose(
        SPAGUARD_PROFILE["acid"],
        current_ph=8.2,
        total_alkalinity=100,
        volume_gallons=335,
        chemical_type=ChemicalType.DRY_ACID,
    )
    assert result is None


def test_label_per_addition_cap_applies_before_rounding() -> None:
    profile = {
        "product_name": "Test acid",
        "method": "label_table",
        "unit": "tsp",
        "round_to": 0.25,
        "per_gallons": 200,
        "max_amount": 0.5,
        "max_per_gallons": 100,
        "dose_table": [{"ph_min": 8.0, "ph_max": 8.4, "amount": 1.5}],
    }
    result = label_table_dose(
        profile,
        current_ph=8.2,
        total_alkalinity=150,
        volume_gallons=335,
        chemical_type=ChemicalType.DRY_ACID,
    )
    assert result is not None
    assert result.amount == 1.75


def test_spaguard_alkalinity_label_rate_scales_exactly() -> None:
    result = label_linear_dose(
        SPAGUARD_PROFILE["alkalinity"],
        current=70,
        target=110,
        volume_gallons=335,
        chemical_type=ChemicalType.BAKING_SODA,
    )
    assert result is not None
    assert result.amount == 16.0
    assert result.unit == "tsp"
    assert result.chemical.name == "SpaGuard Total Alkalinity Increaser"


def test_spaguard_enhanced_shock_label_rate_scales_exactly() -> None:
    result = label_fixed_dose(
        SPAGUARD_PROFILE["shock"],
        volume_gallons=335,
        chemical_type=ChemicalType.DICHLOR,
    )
    assert result.amount == 2.0
    assert result.unit == "tbsp"
    assert result.chemical.name == "SpaGuard Enhanced Shock"
