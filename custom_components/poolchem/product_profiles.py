"""Product label profiles for label-backed chemical doses.

Profiles are deliberately data-driven: Pool Chem supplies chemistry readings and
the selected product's label supplies the dose rule. This keeps product-specific
label rates separate from generic chemical strength assumptions.
"""

from __future__ import annotations

import json
import math
from typing import Any

from pypoolchem.dosing.calculator import DosingResult
from pypoolchem.dosing.chemicals import Chemical, ChemicalType, get_chemical

SPAGUARD_SPA_PROFILE: dict[str, Any] = {
    "acid": {
        "product_name": "SpaGuard pH Decreaser",
        "active_ingredient": "Sodium bisulfate",
        "strength_percent": 93.2,
        "chemical_type": "dry_acid",
        "method": "label_table",
        "unit": "tsp",
        "round_to": 0.25,
        "per_gallons": 200,
        "minimum_total_alkalinity": 125,
        "wait_minutes": 30,
        "label_source": "SpaGuard package directions",
        "dose_table": [
            {"ph_min": 7.6, "ph_max": 7.8, "amount": 0.5},
            {"ph_min": 7.8, "ph_max": 8.0, "amount": 0.75},
            {"ph_min": 8.0, "ph_max": 8.4, "amount": 1.5},
            {"ph_min": 8.4, "ph_max": 14.0, "amount": 2.0},
        ],
    },
    "alkalinity": {
        "product_name": "SpaGuard Total Alkalinity Increaser",
        "active_ingredient": "Sodium bicarbonate",
        "strength_percent": 100,
        "chemical_type": "baking_soda",
        "method": "label_linear",
        "amount": 3,
        "unit": "tsp",
        "round_to": 0.25,
        "per_gallons": 100,
        "raises_ppm": 25,
        "label_source": "SpaGuard package directions",
    },
    "shock": {
        "product_name": "SpaGuard Enhanced Shock",
        "active_ingredient": "Dichlor",
        "strength_percent": 58.2,
        "chemical_type": "dichlor",
        "method": "label_fixed",
        "amount": 3,
        "unit": "tbsp",
        "round_to": 0.25,
        "per_gallons": 500,
        "wait_minutes": 30,
        "label_source": "SpaGuard package directions",
    },
}

_PRODUCT_CHEMICAL_TYPES: dict[str, set[ChemicalType]] = {
    "acid": {
        ChemicalType.MURIATIC_ACID_14_5,
        ChemicalType.MURIATIC_ACID_15_7,
        ChemicalType.MURIATIC_ACID_20,
        ChemicalType.MURIATIC_ACID_28_3,
        ChemicalType.MURIATIC_ACID_31_45,
        ChemicalType.MURIATIC_ACID_34_6,
        ChemicalType.DRY_ACID,
    },
    "ph_up": {ChemicalType.SODA_ASH, ChemicalType.BORAX},
    "alkalinity": {ChemicalType.BAKING_SODA},
    "chlorine": {
        ChemicalType.BLEACH_6,
        ChemicalType.BLEACH_8_25,
        ChemicalType.BLEACH_10,
        ChemicalType.BLEACH_12_5,
        ChemicalType.CAL_HYPO_48,
        ChemicalType.CAL_HYPO_53,
        ChemicalType.CAL_HYPO_65,
        ChemicalType.CAL_HYPO_73,
        ChemicalType.DICHLOR,
        ChemicalType.TRICHLOR,
        ChemicalType.LITHIUM_HYPO,
        ChemicalType.CHLORINE_GAS,
    },
    "calcium": {
        ChemicalType.CALCIUM_CHLORIDE_ANHYDROUS,
        ChemicalType.CALCIUM_CHLORIDE_DIHYDRATE,
    },
    "cya": {ChemicalType.CYA_GRANULAR, ChemicalType.CYA_LIQUID},
    "salt": {ChemicalType.POOL_SALT},
    "borates": {
        ChemicalType.BORAX_BORATE,
        ChemicalType.BORIC_ACID,
        ChemicalType.SODIUM_TETRABORATE_PENTAHYDRATE,
    },
    "shock": {
        ChemicalType.CAL_HYPO_48,
        ChemicalType.CAL_HYPO_53,
        ChemicalType.CAL_HYPO_65,
        ChemicalType.CAL_HYPO_73,
        ChemicalType.DICHLOR,
        ChemicalType.TRICHLOR,
        ChemicalType.LITHIUM_HYPO,
        ChemicalType.CHLORINE_GAS,
    },
}
_SUPPORTED_DOSE_UNITS = {
    "oz",
    "fl oz",
    "fl_oz",
    "tsp",
    "tbsp",
    "cup",
    "cups",
    "lb",
    "lbs",
    "g",
    "kg",
    "mL",
    "ml",
}


def parse_product_profiles(value: str | dict[str, Any] | None) -> dict[str, Any]:
    """Parse and validate the product profile options JSON."""
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        try:
            profiles = json.loads(value)
        except json.JSONDecodeError as err:
            raise ValueError("Product profiles must be valid JSON") from err
    else:
        profiles = value
    if not isinstance(profiles, dict):
        raise ValueError("Product profiles must be a JSON object")

    for category, profile in profiles.items():
        if category not in {
            "acid",
            "ph_up",
            "alkalinity",
            "chlorine",
            "calcium",
            "cya",
            "salt",
            "borates",
            "shock",
        }:
            raise ValueError(f"Unsupported product category: {category}")
        if not isinstance(profile, dict) or not profile.get("product_name"):
            raise ValueError(f"{category} profile requires product_name")
        if profile.get("chemical_type") is not None:
            try:
                chemical_type = ChemicalType(profile["chemical_type"])
            except ValueError as err:
                raise ValueError(f"{category} has an unknown chemical_type") from err
            if chemical_type not in _PRODUCT_CHEMICAL_TYPES[category]:
                raise ValueError(f"{category} has an incompatible chemical_type")
        if profile.get("strength_percent") is not None and not (
            0 < float(profile["strength_percent"]) <= 100
        ):
            raise ValueError("strength_percent must be greater than 0 and at most 100")
        if (
            profile.get("unit") is not None
            and profile["unit"] not in _SUPPORTED_DOSE_UNITS
        ):
            raise ValueError(f"{category} has an unsupported dose unit")
        method = profile.get("method")
        if method not in {"label_table", "label_linear", "label_fixed"}:
            raise ValueError(f"{category} profile has unsupported method")
        allowed_methods = {
            "acid": {"label_table"},
            "ph_up": {"label_table"},
            "alkalinity": {"label_linear"},
            "chlorine": {"label_linear"},
            "calcium": {"label_linear"},
            "cya": {"label_linear"},
            "salt": {"label_linear"},
            "borates": {"label_linear"},
            "shock": {"label_fixed"},
        }
        if method not in allowed_methods[category]:
            raise ValueError(f"{category} profile cannot use {method}")
        if method == "label_table":
            rows = profile.get("dose_table")
            if not isinstance(rows, list) or not rows:
                raise ValueError(f"{category} label_table requires dose_table rows")
            for row in rows:
                if not isinstance(row, dict) or not all(
                    key in row for key in ("ph_min", "ph_max", "amount")
                ):
                    raise ValueError("Dose table rows require ph_min, ph_max, amount")
                if row["ph_min"] >= row["ph_max"] or row["amount"] <= 0:
                    raise ValueError("Dose table ranges and amounts must be positive")
        if method == "label_linear":
            required = ("amount", "per_gallons", "raises_ppm")
            if any(profile.get(key) is None for key in required):
                raise ValueError(f"{category} label_linear requires {required}")
            if any(float(profile[key]) <= 0 for key in required):
                raise ValueError("Label rate values must be positive")
        if method == "label_fixed":
            if profile.get("amount") is None or profile.get("per_gallons") is None:
                raise ValueError(
                    f"{category} label_fixed requires amount and per_gallons"
                )
            if float(profile["amount"]) <= 0 or float(profile["per_gallons"]) <= 0:
                raise ValueError("Label dose values must be positive")
        if profile.get("wait_minutes", 0) < 0:
            raise ValueError("wait_minutes cannot be negative")
        if profile.get("round_to") is not None and float(profile["round_to"]) <= 0:
            raise ValueError("round_to must be positive")
        if (profile.get("max_amount") is None) != (
            profile.get("max_per_gallons") is None
        ):
            raise ValueError("max_amount and max_per_gallons must be set together")
        if profile.get("max_amount") is not None and (
            float(profile["max_amount"]) <= 0 or float(profile["max_per_gallons"]) <= 0
        ):
            raise ValueError("Maximum dose values must be positive")
    return profiles


def load_product_profiles(
    preset: str | None, custom_value: str | dict[str, Any] | None
) -> dict[str, Any]:
    """Load built-in product data and overlay explicit household profiles."""
    profiles = SPAGUARD_SPA_PROFILE.copy() if preset == "spaguard_spa" else {}
    profiles.update(parse_product_profiles(custom_value))
    return profiles


def product_unit(profiles: dict[str, Any], category: str, fallback: str) -> str:
    """Return the configured product measure or the calculator's native unit."""
    return str(profiles.get(category, {}).get("unit", fallback))


def profile_chemical_type(
    profile: dict[str, Any], fallback: ChemicalType
) -> ChemicalType:
    """Return the profile's active chemical type, when explicitly configured."""
    chemical_type = profile.get("chemical_type")
    return ChemicalType(chemical_type) if chemical_type else fallback


def profile_notes(profile: dict[str, Any], notes: str) -> str:
    """Append the selected product's label identity to recommendation notes."""
    details = [
        str(profile[key])
        for key in ("active_ingredient", "strength_percent", "label_source")
        if profile.get(key) is not None
    ]
    return f"{notes} Product: {profile['product_name']}." + (
        f" Label data: {', '.join(details)}." if details else ""
    )


def _round_amount(amount: float, profile: dict[str, Any]) -> float:
    """Round to a product's practical measuring increment, if configured."""
    increment = profile.get("round_to")
    if increment is None:
        return round(amount, 2)
    step = float(increment)
    return round(math.floor(amount / step + 0.5 + 1e-9) * step, 2)


def _cap_amount(amount: float, profile: dict[str, Any], volume_gallons: float) -> float:
    """Apply an optional product-label maximum per addition."""
    maximum = profile.get("max_amount")
    if maximum is None:
        return amount
    scaled_maximum = float(maximum) * volume_gallons / float(profile["max_per_gallons"])
    return min(amount, scaled_maximum)


def label_table_dose(
    profile: dict[str, Any],
    *,
    current_ph: float,
    total_alkalinity: float,
    volume_gallons: float,
    chemical_type: ChemicalType,
) -> DosingResult | None:
    """Return a label-table dose; return None when label constraints do not fit."""
    minimum_ta = profile.get("minimum_total_alkalinity")
    if minimum_ta is not None and total_alkalinity < float(minimum_ta):
        return None

    row = next(
        (
            item
            for item in profile["dose_table"]
            if float(item["ph_min"]) <= current_ph <= float(item["ph_max"])
        ),
        None,
    )
    if row is None:
        return None

    base_volume = float(profile.get("per_gallons", 200))
    amount = float(row["amount"]) * volume_gallons / base_volume
    amount = _cap_amount(amount, profile, volume_gallons)
    unit = str(profile.get("unit", "tsp"))
    chemical = get_chemical(chemical_type).model_copy(
        update={"name": profile["product_name"], "unit": unit}
    )
    return DosingResult(
        chemical=chemical,
        amount=_round_amount(amount, profile),
        unit=unit,
        notes=profile_notes(
            profile,
            f"Label dose scaled from {base_volume:g} gallons; "
            f"wait {int(profile.get('wait_minutes', 0))} minutes.",
        ),
    )


def label_linear_dose(
    profile: dict[str, Any],
    *,
    current: float,
    target: float,
    volume_gallons: float,
    chemical_type: ChemicalType,
) -> DosingResult | None:
    """Calculate a linear label dose, such as alkalinity raiser."""
    if target <= current:
        return None
    amount = (
        (target - current)
        / float(profile["raises_ppm"])
        * float(profile["amount"])
        * volume_gallons
        / float(profile["per_gallons"])
    )
    amount = _cap_amount(amount, profile, volume_gallons)
    unit = str(profile.get("unit", "tbsp"))
    chemical = get_chemical(chemical_type).model_copy(
        update={"name": profile["product_name"], "unit": unit}
    )
    return DosingResult(
        chemical=chemical,
        amount=_round_amount(amount, profile),
        unit=unit,
        notes=profile_notes(
            profile,
            f"Label rate scaled from {float(profile['per_gallons']):g} gallons "
            f"per {float(profile['raises_ppm']):g} ppm.",
        ),
    )


def label_fixed_dose(
    profile: dict[str, Any],
    *,
    volume_gallons: float,
    chemical_type: ChemicalType,
) -> DosingResult:
    """Calculate a fixed label dose, such as routine shock."""
    base_volume = float(profile["per_gallons"])
    amount = float(profile["amount"]) * volume_gallons / base_volume
    amount = _cap_amount(amount, profile, volume_gallons)
    unit = str(profile.get("unit", "oz"))
    chemical = get_chemical(chemical_type).model_copy(
        update={"name": profile["product_name"], "unit": unit}
    )
    return DosingResult(
        chemical=chemical,
        amount=_round_amount(amount, profile),
        unit=unit,
        notes=profile_notes(
            profile,
            f"Label dose scaled from {base_volume:g} gallons; "
            f"wait {int(profile.get('wait_minutes', 0))} minutes.",
        ),
    )


def chemical_with_product_name(
    chemical_type: ChemicalType, product_name: str
) -> Chemical:
    """Copy a core chemical entry with a user-selected product name."""
    return get_chemical(chemical_type).model_copy(update={"name": product_name})
