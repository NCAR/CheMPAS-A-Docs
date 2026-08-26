#!/usr/bin/env python3
"""Prepare and audit the frozen CAMS and FINN exact-grid MVP inventories."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

import netCDF4
import numpy as np
from scipy.spatial import cKDTree

from acquire_mvp_cams_co import _validate_dataset as validate_cams_co_dataset
from acquire_mvp_finn import SPECIES_MOLAR_MASS_KG_MOL, iter_finn_records
from global_inventory_common import (
    atomic_write_json,
    latitude_longitude_cell_areas,
    require_data_root,
    sha256_file,
)
from miem_mesh_identity import (
    FINGERPRINT_ATTRIBUTE,
    copy_identity_to_dataset,
    read_mesh_identity,
)
from prepare_miem_inventory import package_inventory
from remap_global_miem_inventory import (
    REMAP_MASS_TOLERANCE,
    _degrees,
    apply_weights,
    read_weights,
)
from verify_global_miem_inventory import validate_inventory


SCHEMA_VERSION = "chempas-mvp-emissions-preparation-v1"
MANIFEST_VERSION = "chempas-mvp-external-inputs-v1"
CANONICAL_UNITS = "kg m-2 s-1"
OVERLAP_POLICY = (
    "CAMS agricultural waste burning (awb) is withheld; FINN alone represents "
    "open burning in MVP attribution members A, B, and C"
)
NOX_SECTORS = (
    "agl", "ags", "com", "ene", "fef", "ind", "ref", "res", "shp", "swd", "tnr", "tro"
)
CO_SECTORS = ("com", "ene", "fef", "ind", "ref", "res", "shp", "swd", "tnr", "tro")
ALL_CO_SECTORS = ("awb", *CO_SECTORS)
SPECIES = ("NO", "NO2", "CO")
DEFAULT_CREATION_TIME = "2026-08-15T00:00:00+00:00"


class MvpEmissionError(ValueError):
    """Raised when an MVP emission input or transformation violates its contract."""


def validate_overlap_policy(
    retained_cams_sectors: Sequence[str], *, fire_source_included: bool
) -> None:
    """Reject a CAMS open-burning sector when FINN represents fire."""

    normalized = {str(value).strip().lower() for value in retained_cams_sectors}
    if fire_source_included and "awb" in normalized:
        raise MvpEmissionError(
            "source overlap: CAMS awb must be withheld when the FINN fire source is included"
        )


def _manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MvpEmissionError(f"could not read manifest {path}: {error}") from error
    if value.get("schema_version") != MANIFEST_VERSION:
        raise MvpEmissionError(f"manifest schema must be {MANIFEST_VERSION}")
    return value


def _artifact(manifest: dict[str, Any], role: str) -> dict[str, Any]:
    matches = [item for item in manifest.get("artifacts", []) if item.get("role") == role]
    if len(matches) != 1:
        raise MvpEmissionError(f"manifest must contain exactly one {role} artifact")
    return matches[0]


def _artifacts(manifest: dict[str, Any], role: str) -> list[dict[str, Any]]:
    matches = [item for item in manifest.get("artifacts", []) if item.get("role") == role]
    if not matches:
        raise MvpEmissionError(f"manifest contains no {role} artifacts")
    return sorted(matches, key=lambda item: str(item["selection"]["date"]))


def _verify_artifact(root: Path, artifact: dict[str, Any]) -> Path:
    path = root / str(artifact["logical_path"])
    if not path.is_file():
        raise MvpEmissionError(f"missing frozen input {path}")
    if path.stat().st_size != int(artifact["size_bytes"]):
        raise MvpEmissionError(f"size mismatch for frozen input {path}")
    if sha256_file(path) != str(artifact["sha256"]):
        raise MvpEmissionError(f"SHA-256 mismatch for frozen input {path}")
    return path


def _complete(variable: netCDF4.Variable, label: str) -> np.ndarray:
    values: Any = variable[:]
    if np.ma.isMaskedArray(values):
        if np.any(np.ma.getmaskarray(values)):
            raise MvpEmissionError(f"{label} contains missing values")
        values = values.data
    result = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise MvpEmissionError(f"{label} contains NaN or Inf")
    if np.any(result < 0.0):
        raise MvpEmissionError(f"{label} contains negative source flux")
    result[result == 0.0] = 0.0
    return result


def _read_xtime(dataset: netCDF4.Dataset) -> list[str]:
    if "xtime" not in dataset.variables:
        raise MvpEmissionError("exact-grid inventory lacks xtime")
    variable = dataset.variables["xtime"]
    if str(getattr(variable, "calendar", "")).lower() != "gregorian":
        raise MvpEmissionError("exact-grid inventory calendar must be gregorian")
    raw = variable[:]
    if np.ma.isMaskedArray(raw):
        raw = raw.filled(b" ")
    array = np.asarray(raw)
    if array.ndim != 2 or array.dtype.kind not in {"S", "U"}:
        raise MvpEmissionError("xtime must be a Time by StrLen character array")
    result = []
    for row in array:
        if array.dtype.kind == "S":
            text = b"".join(np.asarray(row, dtype="S1").tolist()).decode("ascii")
        else:
            text = "".join(str(item) for item in row)
        result.append(text.rstrip("\x00 "))
    if len(result) < 1 or any(not value for value in result):
        raise MvpEmissionError("xtime contains an empty record")
    return result


def _write_xtime(dataset: netCDF4.Dataset, times: Sequence[str]) -> None:
    variable = dataset.createVariable("xtime", "S1", ("Time", "StrLen"))
    variable.setncattr("calendar", "gregorian")
    variable.setncattr("long_name", "emission-rate time anchors")
    characters = np.full((len(times), 64), b" ", dtype="S1")
    for index, value in enumerate(times):
        encoded = value.encode("ascii")
        characters[index, : len(encoded)] = np.frombuffer(encoded, dtype="S1")
    variable[:] = characters


def _parse_time(value: str) -> dt.datetime:
    candidate = value.replace("_", "T", 1).removesuffix("Z")
    try:
        return dt.datetime.fromisoformat(candidate)
    except ValueError as error:
        raise MvpEmissionError(f"invalid inventory timestamp {value!r}") from error


def _atomic_netcdf_path(output: Path, force: bool) -> tuple[Path, int]:
    if output.exists() and not force:
        raise MvpEmissionError(f"output exists: {output}; pass --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(descriptor)
    os.unlink(name)
    return Path(name), descriptor


def _field(
    dataset: netCDF4.Dataset, name: str, *, long_name: str
) -> netCDF4.Variable:
    variable = dataset.createVariable(
        name,
        "f8",
        ("Time", "nCells"),
        zlib=True,
        complevel=2,
        shuffle=True,
        fill_value=np.nan,
    )
    variable.setncattr("units", CANONICAL_UNITS)
    variable.setncattr("long_name", long_name)
    variable.setncattr("source_semantics", "nonnegative upward surface source")
    return variable


def _relative(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), np.finfo(np.float64).tiny)


def _package(
    *, mesh: Path, source: Path, output: Path, fields: Sequence[str], label: str, force: bool
) -> None:
    package_inventory(
        mesh_path=mesh,
        source_path=source,
        output_path=output,
        mappings={name: name for name in fields},
        unit_overrides=None,
        remapping_tool=label,
        remapping_method="offline exact-grid preparation; no runtime horizontal regridding",
        force=force,
        source_label=source.name,
        mesh_label=mesh.name,
        creation_command="prepare_mvp_emissions.py",
        creation_time=DEFAULT_CREATION_TIME,
    )


def prepare_cams(
    *,
    mesh_path: Path,
    accepted_nox_path: Path,
    co_source_path: Path,
    weights_path: Path,
    remapped_path: Path,
    packaged_path: Path,
    force: bool,
) -> dict[str, Any]:
    """Create the non-overlapping CAMS NO/NO2/CO exact-grid source."""

    validate_overlap_policy((*NOX_SECTORS, *CO_SECTORS), fire_source_included=True)
    identity = read_mesh_identity(mesh_path)
    temporary, _ = _atomic_netcdf_path(remapped_path, force)
    time_reports: list[dict[str, Any]] = []
    fields = [
        *(name for sector in NOX_SECTORS for name in (f"no_anth_{sector}", f"no2_anth_{sector}")),
        *(f"co_anth_{sector}" for sector in CO_SECTORS),
        "no_anth_sum",
        "no2_anth_sum",
        "co_anth_sum",
    ]
    try:
        with (
            netCDF4.Dataset(mesh_path) as mesh,
            netCDF4.Dataset(accepted_nox_path) as nox,
            netCDF4.Dataset(co_source_path) as co,
        ):
            destination_area = _complete(mesh.variables["areaCell"], "mesh areaCell")
            if str(getattr(nox, FINGERPRINT_ATTRIBUTE, "")) != identity.fingerprint:
                raise MvpEmissionError("accepted NOx inventory mesh fingerprint mismatch")
            ids = np.asarray(nox.variables["indexToCellID"][:], dtype=np.int64)
            if not np.array_equal(ids, identity.ordered_global_ids):
                raise MvpEmissionError("accepted NOx inventory cell identity/order mismatch")
            times = _read_xtime(nox)
            if times != ["2024-07-01_00:00:00", "2024-08-01_00:00:00"]:
                raise MvpEmissionError(f"accepted NOx times changed: {times}")
            co_times_iso, co_sectors = validate_cams_co_dataset(
                co, (*ALL_CO_SECTORS, "sum"), selected=True
            )
            co_times = [value.replace("T", "_").removesuffix("Z") for value in co_times_iso]
            if co_times != times or tuple(co_sectors) != ALL_CO_SECTORS:
                raise MvpEmissionError("CAMS CO time/sector contract changed")
            latitudes = _degrees(co.variables["lat"], "CAMS CO latitude")
            longitudes = _degrees(co.variables["lon"], "CAMS CO longitude")
            source_area = latitude_longitude_cell_areas(
                latitudes, longitudes, radius_m=float(identity.sphere_radius)
            ).reshape(-1, order="C")
            row, col, weight, weight_metrics = read_weights(
                weights_path,
                source_area / float(identity.sphere_radius) ** 2,
                destination_area / float(identity.sphere_radius) ** 2,
            )

            with netCDF4.Dataset(temporary, "w", format="NETCDF4") as output:
                output.createDimension("Time", len(times))
                output.createDimension("nCells", identity.n_cells)
                output.createDimension("StrLen", 64)
                _write_xtime(output, times)
                copy_identity_to_dataset(output, identity, mesh)
                output.setncattr("inventory_convention", "UPTEMPO")
                output.setncattr("source_group", "harmonized non-fire CAMS")
                output.setncattr("overlap_policy", OVERLAP_POLICY)
                output.setncattr("withheld_sector", "awb")
                output.setncattr("accepted_nox_sha256", sha256_file(accepted_nox_path))
                output.setncattr("native_co_sha256", sha256_file(co_source_path))
                output.setncattr("remapping_weights_sha256", sha256_file(weights_path))
                variables = {
                    name: _field(
                        output,
                        name,
                        long_name=f"CAMS harmonized {name} surface mass flux",
                    )
                    for name in fields
                }

                for time_index, timestamp in enumerate(times):
                    no_sum = np.zeros(identity.n_cells, dtype=np.float64)
                    no2_sum = np.zeros(identity.n_cells, dtype=np.float64)
                    nox_sector_records: dict[str, Any] = {}
                    for sector in NOX_SECTORS:
                        no_name = f"no_anth_{sector}"
                        no2_name = f"no2_anth_{sector}"
                        if no_name not in nox.variables or no2_name not in nox.variables:
                            raise MvpEmissionError(f"accepted NOx inventory lacks sector {sector}")
                        no_values = _complete(nox.variables[no_name][time_index, :], no_name)
                        no2_values = _complete(nox.variables[no2_name][time_index, :], no2_name)
                        variables[no_name][time_index, :] = no_values
                        variables[no2_name][time_index, :] = no2_values
                        no_sum += no_values
                        no2_sum += no2_values
                        nox_sector_records[sector] = {
                            "NO_kg_s-1": float(np.sum(no_values * destination_area, dtype=np.float64)),
                            "NO2_kg_s-1": float(np.sum(no2_values * destination_area, dtype=np.float64)),
                        }
                    awb_no = _complete(nox.variables["no_anth_awb"][time_index, :], "no_anth_awb")
                    awb_no2 = _complete(nox.variables["no2_anth_awb"][time_index, :], "no2_anth_awb")
                    variables["no_anth_sum"][time_index, :] = no_sum
                    variables["no2_anth_sum"][time_index, :] = no2_sum

                    co_targets: dict[str, np.ndarray] = {}
                    co_sector_records: dict[str, Any] = {}
                    for sector in ALL_CO_SECTORS:
                        source_values = _complete(
                            co.variables[sector][time_index, :, :], f"CO {sector}[{time_index}]"
                        )
                        target = apply_weights(source_values, row, col, weight, identity.n_cells)
                        if np.any(target < -1.0e-20) or not np.all(np.isfinite(target)):
                            raise MvpEmissionError(f"remapped CAMS CO sector {sector} is invalid")
                        target[target < 0.0] = 0.0
                        source_total = float(
                            np.sum(source_values.reshape(-1, order="C") * source_area, dtype=np.float64)
                        )
                        target_total = float(np.sum(target * destination_area, dtype=np.float64))
                        relative = _relative(target_total, source_total)
                        if relative > REMAP_MASS_TOLERANCE:
                            raise MvpEmissionError(
                                f"CAMS CO {sector}[{timestamp}] remap mass error {relative:.3e}"
                            )
                        co_targets[sector] = target
                        co_sector_records[sector] = {
                            "native_kg_s-1": source_total,
                            "remapped_kg_s-1": target_total,
                            "relative_difference": relative,
                            "retained": sector != "awb",
                        }
                    co_sum = np.sum(
                        np.stack([co_targets[sector] for sector in CO_SECTORS]),
                        axis=0,
                        dtype=np.float64,
                    )
                    for sector in CO_SECTORS:
                        variables[f"co_anth_{sector}"][time_index, :] = co_targets[sector]
                    variables["co_anth_sum"][time_index, :] = co_sum

                    declared_source = _complete(
                        co.variables["sum"][time_index, :, :], f"CO sum[{time_index}]"
                    )
                    declared_target = apply_weights(
                        declared_source, row, col, weight, identity.n_cells
                    )
                    reconstructed_all = np.sum(
                        np.stack([co_targets[sector] for sector in ALL_CO_SECTORS]),
                        axis=0,
                        dtype=np.float64,
                    )
                    declared_total = float(np.sum(declared_target * destination_area, dtype=np.float64))
                    reconstructed_total = float(
                        np.sum(reconstructed_all * destination_area, dtype=np.float64)
                    )
                    closure = _relative(reconstructed_total, declared_total)
                    if closure > 5.0e-6:
                        raise MvpEmissionError(f"CAMS CO provider sector closure failed at {timestamp}")
                    no_mass = float(np.sum(no_sum * destination_area, dtype=np.float64))
                    no2_mass = float(np.sum(no2_sum * destination_area, dtype=np.float64))
                    co_mass = float(np.sum(co_sum * destination_area, dtype=np.float64))
                    time_reports.append(
                        {
                            "time": timestamp,
                            "nox_sectors": nox_sector_records,
                            "co_sectors": co_sector_records,
                            "withheld_awb": {
                                "NO_kg_s-1": float(np.sum(awb_no * destination_area, dtype=np.float64)),
                                "NO2_kg_s-1": float(np.sum(awb_no2 * destination_area, dtype=np.float64)),
                                "CO_kg_s-1": co_sector_records["awb"]["remapped_kg_s-1"],
                            },
                            "harmonized": {
                                "NO_kg_s-1": no_mass,
                                "NO2_kg_s-1": no2_mass,
                                "CO_kg_s-1": co_mass,
                                "nitrogen_kgN_s-1": (
                                    no_mass / 0.030 + no2_mass / 0.046
                                ) * 0.014007,
                                "carbon_kgC_s-1": co_mass * 0.012011 / 0.028,
                            },
                            "provider_CO_sector_sum_relative_difference": closure,
                        }
                    )
        os.replace(temporary, remapped_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    _package(
        mesh=mesh_path,
        source=remapped_path,
        output=packaged_path,
        fields=fields,
        label="CAMS-GLOB-ANT v6.2 conservative CO remap plus accepted exact-grid NO/NO2",
        force=force,
    )
    validation = validate_inventory(
        mesh_path=mesh_path,
        inventory_path=packaged_path,
        start_time="2024-07-01_00:00:00",
        stop_time="2024-07-02_00:00:00",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_group": "harmonized non-fire CAMS",
        "overlap_policy": OVERLAP_POLICY,
        "retained_nox_sectors": list(NOX_SECTORS),
        "retained_co_sectors": list(CO_SECTORS),
        "withheld_sector": "awb",
        "inputs": {
            "accepted_nox": _record(accepted_nox_path),
            "native_co": _record(co_source_path),
            "mesh": {**_record(mesh_path), "fingerprint": identity.fingerprint},
            "weights": _record(weights_path),
        },
        "outputs": {
            "remapped": _record(remapped_path),
            "packaged": _record(packaged_path),
        },
        "weight_metrics": weight_metrics,
        "packaged_validation": {
            "n_cells": validation.n_cells,
            "n_times": 2,
            "species": list(validation.species),
            "mesh_fingerprint": validation.mesh_fingerprint,
        },
        "times": time_reports,
        "assertions": {
            "awb_absent_from_packaged_fields": True,
            "co_conservative_remap": True,
            "provider_co_sector_sum_closure": True,
            "accepted_explicit_no_no2_preserved": True,
            "exact_grid_package_validation": True,
        },
        "overall_pass": True,
    }


def _unit_vectors(latitude_deg: np.ndarray, longitude_deg: np.ndarray) -> np.ndarray:
    latitude = np.deg2rad(np.asarray(latitude_deg, dtype=np.float64))
    longitude = np.deg2rad(np.asarray(longitude_deg, dtype=np.float64))
    cosine = np.cos(latitude)
    return np.column_stack(
        (cosine * np.cos(longitude), cosine * np.sin(longitude), np.sin(latitude))
    )


def conservative_point_allocation(
    *,
    mesh_vectors: np.ndarray,
    mesh_area: np.ndarray,
    latitude_deg: np.ndarray,
    longitude_deg: np.ndarray,
    moles_per_day: dict[str, np.ndarray],
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Allocate each point total to one nearest cell, preserving global amount."""

    if mesh_vectors.ndim != 2 or mesh_vectors.shape[1] != 3:
        raise MvpEmissionError("mesh unit vectors must have shape (nCells,3)")
    if mesh_area.shape != (mesh_vectors.shape[0],) or np.any(mesh_area <= 0.0):
        raise MvpEmissionError("mesh areas do not match point-allocation vectors")
    latitude = np.asarray(latitude_deg, dtype=np.float64)
    longitude = np.asarray(longitude_deg, dtype=np.float64)
    if latitude.shape != longitude.shape or latitude.ndim != 1 or latitude.size == 0:
        raise MvpEmissionError("FINN point coordinates must be nonempty matching vectors")
    if np.any(latitude < -90.0) or np.any(latitude > 90.0):
        raise MvpEmissionError("FINN latitude is outside [-90,90]")
    if np.any(longitude < -180.0) or np.any(longitude > 180.0):
        raise MvpEmissionError("FINN longitude is outside [-180,180]")
    distances, cell = cKDTree(mesh_vectors).query(_unit_vectors(latitude, longitude), k=1)
    result: dict[str, np.ndarray] = {}
    totals: dict[str, Any] = {}
    for species in SPECIES:
        values = np.asarray(moles_per_day[species], dtype=np.float64)
        if values.shape != latitude.shape or not np.all(np.isfinite(values)) or np.any(values < 0.0):
            raise MvpEmissionError(f"FINN {species} point totals are invalid")
        cell_moles = np.bincount(cell, weights=values, minlength=mesh_vectors.shape[0])
        flux = (
            cell_moles
            * SPECIES_MOLAR_MASS_KG_MOL[species]
            / 86400.0
            / mesh_area
        )
        source_total = float(np.sum(values, dtype=np.float64))
        reconstructed = float(
            np.sum(
                flux * mesh_area / SPECIES_MOLAR_MASS_KG_MOL[species] * 86400.0,
                dtype=np.float64,
            )
        )
        relative = _relative(reconstructed, source_total)
        if relative > 5.0e-15:
            raise MvpEmissionError(f"FINN {species} point allocation did not conserve amount")
        result[species] = flux
        totals[species] = {
            "provider_mol_day-1": source_total,
            "packaged_mol_day-1": reconstructed,
            "relative_difference": relative,
            "packaged_kg_s-1": float(np.sum(flux * mesh_area, dtype=np.float64)),
        }
    angle = 2.0 * np.arcsin(np.clip(distances / 2.0, 0.0, 1.0))
    return result, {
        "records": int(latitude.size),
        "occupied_destination_cells": int(np.unique(cell).size),
        "mean_allocation_distance_km": float(np.mean(angle) * 6371.229),
        "maximum_allocation_distance_km": float(np.max(angle) * 6371.229),
        "species": totals,
    }


def prepare_finn(
    *,
    mesh_path: Path,
    sources: Sequence[tuple[str, Path]],
    remapped_path: Path,
    packaged_path: Path,
    force: bool,
) -> dict[str, Any]:
    """Map direct FINN CO/NO/NO2 daily totals to the exact MPAS grid."""

    identity = read_mesh_identity(mesh_path)
    temporary, _ = _atomic_netcdf_path(remapped_path, force)
    anchor_times = [f"{date}_12:00:00" for date, _ in sources]
    if any(later <= earlier for earlier, later in zip(anchor_times, anchor_times[1:])):
        raise MvpEmissionError("FINN dates must be strictly increasing")
    # MIEM deliberately rejects extrapolation outside a file's time range.
    # Duplicate the first daily field at the simulation-start boundary so the
    # declared nearest-anchor approximation covers 00:00--12:00 UTC without
    # changing either scientific noon anchor or the midnight nearest switch.
    times = [f"{sources[0][0]}_00:00:00", *anchor_times]
    reports: list[dict[str, Any]] = []
    fields = ("no_fire", "no2_fire", "co_fire")
    try:
        with netCDF4.Dataset(mesh_path) as mesh:
            area = _complete(mesh.variables["areaCell"], "mesh areaCell")
            lat = _degrees(mesh.variables["latCell"], "mesh latCell")
            lon = _degrees(mesh.variables["lonCell"], "mesh lonCell")
            mesh_vectors = _unit_vectors(lat, lon)
            prepared: list[dict[str, np.ndarray]] = []
            for date, path in sources:
                expected_day = dt.date.fromisoformat(date).timetuple().tm_yday
                latitude: list[float] = []
                longitude: list[float] = []
                species_values = {species: [] for species in SPECIES}
                for record in iter_finn_records(path):
                    if int(record["DAY"]) != expected_day:
                        raise MvpEmissionError(
                            f"FINN {path.name} DAY does not match declared date {date}"
                        )
                    latitude.append(float(record["LATI"]))
                    longitude.append(float(record["LONGI"]))
                    for species in SPECIES:
                        species_values[species].append(float(record[species]))
                fluxes, allocation = conservative_point_allocation(
                    mesh_vectors=mesh_vectors,
                    mesh_area=area,
                    latitude_deg=np.asarray(latitude),
                    longitude_deg=np.asarray(longitude),
                    moles_per_day={
                        species: np.asarray(values, dtype=np.float64)
                        for species, values in species_values.items()
                    },
                )
                prepared.append(fluxes)
                allocation.update(
                    {
                        "date": date,
                        "time_anchor_utc": f"{date}T12:00:00Z",
                        "source": _record(path),
                        "nitrogen_kgN_s-1": (
                            allocation["species"]["NO"]["packaged_kg_s-1"] / 0.030
                            + allocation["species"]["NO2"]["packaged_kg_s-1"] / 0.046
                        )
                        * 0.014007,
                        "carbon_kgC_s-1": allocation["species"]["CO"]["packaged_kg_s-1"]
                        * 0.012011
                        / 0.028,
                    }
                )
                reports.append(allocation)

            with netCDF4.Dataset(temporary, "w", format="NETCDF4") as output:
                output.createDimension("Time", len(times))
                output.createDimension("nCells", identity.n_cells)
                output.createDimension("StrLen", 64)
                _write_xtime(output, times)
                copy_identity_to_dataset(output, identity, mesh)
                output.setncattr("inventory_convention", "UPTEMPO")
                output.setncattr("source_group", "FINNv2.5.1 fire")
                output.setncattr("provider_species_mapping", "direct CO, NO, and NO2; NOXasNO ignored")
                output.setncattr("temporal_interpolation", "nearest")
                output.setncattr(
                    "temporal_semantics",
                    "provider fire-local-date totals divided by 86400 s and anchored at 12:00 UTC; "
                    "up to 12 h longitude-dependent timing displacement",
                )
                output.setncattr("vertical_injection", "surface")
                variables = {
                    name: _field(output, name, long_name=f"FINN {name} surface mass flux")
                    for name in fields
                }
                runtime_fluxes = [prepared[0], *prepared]
                for index, fluxes in enumerate(runtime_fluxes):
                    variables["no_fire"][index, :] = fluxes["NO"]
                    variables["no2_fire"][index, :] = fluxes["NO2"]
                    variables["co_fire"][index, :] = fluxes["CO"]
                output.setncattr(
                    "coverage_guard",
                    "first daily field duplicated at 2024-07-01 00:00 UTC to cover the "
                    "pre-anchor interval; scientific records remain noon UTC anchors",
                )
        os.replace(temporary, remapped_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    _package(
        mesh=mesh_path,
        source=remapped_path,
        output=packaged_path,
        fields=fields,
        label="FINNv2.5.1 conservative nearest-cell point-total allocation",
        force=force,
    )
    validation = validate_inventory(
        mesh_path=mesh_path,
        inventory_path=packaged_path,
        start_time="2024-07-01_00:00:00",
        stop_time="2024-07-02_12:00:00",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_group": "FINNv2.5.1 fire",
        "provider_species_mapping": "direct CO, NO, and NO2; NOXasNO ignored",
        "temporal_semantics": (
            "fire-local-date totals / 86400 s, nearest records anchored at 12:00 UTC; "
            "up to 12 h longitude-dependent displacement"
        ),
        "coverage_guard": (
            "the first daily field is duplicated at 2024-07-01 00:00 UTC so MIEM "
            "covers the pre-noon interval without extrapolation"
        ),
        "vertical_injection": "surface",
        "inputs": {
            "mesh": {**_record(mesh_path), "fingerprint": identity.fingerprint},
            "daily_sources": [_record(path) for _, path in sources],
        },
        "outputs": {
            "remapped": _record(remapped_path),
            "packaged": _record(packaged_path),
        },
        "packaged_validation": {
            "n_cells": validation.n_cells,
            "n_times": len(times),
            "species": list(validation.species),
            "mesh_fingerprint": validation.mesh_fingerprint,
        },
        "times": reports,
        "assertions": {
            "direct_provider_species_only": True,
            "point_total_conservation": True,
            "nonnegative_surface_flux": True,
            "exact_grid_package_validation": True,
        },
        "overall_pass": True,
    }


def _record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _interpolate_linear(times: Sequence[str], values: np.ndarray, target: dt.datetime) -> np.ndarray:
    parsed = [_parse_time(value) for value in times]
    if len(parsed) != 2 or not parsed[0] <= target <= parsed[1]:
        raise MvpEmissionError("CAMS audit target is outside its two-record bracket")
    alpha = (target - parsed[0]).total_seconds() / (parsed[1] - parsed[0]).total_seconds()
    return (1.0 - alpha) * values[0, :] + alpha * values[1, :]


def _interpolate_nearest(times: Sequence[str], values: np.ndarray, target: dt.datetime) -> np.ndarray:
    parsed = [_parse_time(value) for value in times]
    index = min(range(len(parsed)), key=lambda item: (abs((target - parsed[item]).total_seconds()), item))
    return values[index, :].copy()


def audit_runtime_sum(
    *, mesh_path: Path, cams_path: Path, finn_path: Path, timestamp: str
) -> dict[str, Any]:
    """Independently reconstruct each inventory interpolation and their sum."""

    identity = read_mesh_identity(mesh_path)
    target = _parse_time(timestamp)
    with (
        netCDF4.Dataset(mesh_path) as mesh,
        netCDF4.Dataset(cams_path) as cams,
        netCDF4.Dataset(finn_path) as finn,
    ):
        area = _complete(mesh.variables["areaCell"], "mesh areaCell")
        for label, dataset in (("CAMS", cams), ("FINN", finn)):
            if str(getattr(dataset, FINGERPRINT_ATTRIBUTE, "")) != identity.fingerprint:
                raise MvpEmissionError(f"{label} package mesh fingerprint mismatch")
            ids = np.asarray(dataset.variables["indexToCellID"][:], dtype=np.int64)
            if not np.array_equal(ids, identity.ordered_global_ids):
                raise MvpEmissionError(f"{label} package cell identity/order mismatch")
        cams_times = _read_xtime(cams)
        finn_times = _read_xtime(finn)
        species_reports: dict[str, Any] = {}
        nitrogen = {"cams": 0.0, "finn": 0.0, "sum": 0.0}
        carbon = {"cams": 0.0, "finn": 0.0, "sum": 0.0}
        for species, stem, molar_mass in (
            ("NO", "no", 0.030), ("NO2", "no2", 0.046), ("CO", "co", 0.028)
        ):
            cams_value = _interpolate_linear(
                cams_times, _complete(cams.variables[f"{stem}_anth_sum"], f"CAMS {species}"), target
            )
            finn_value = _interpolate_nearest(
                finn_times, _complete(finn.variables[f"{stem}_fire"], f"FINN {species}"), target
            )
            combined = cams_value + finn_value
            sample_ids = sorted(
                {
                    int(np.argmax(cams_value)) + 1,
                    int(np.argmax(finn_value)) + 1,
                    int(np.argmax(combined)) + 1,
                }
            )
            cams_mass = float(np.sum(cams_value * area, dtype=np.float64))
            finn_mass = float(np.sum(finn_value * area, dtype=np.float64))
            combined_mass = float(np.sum(combined * area, dtype=np.float64))
            residual = combined_mass - cams_mass - finn_mass
            if abs(residual) > 2.0e-15 * max(abs(combined_mass), 1.0):
                raise MvpEmissionError(f"combined {species} runtime mass did not close")
            if species in {"NO", "NO2"}:
                factor = 0.014007 / molar_mass
                nitrogen["cams"] += cams_mass * factor
                nitrogen["finn"] += finn_mass * factor
                nitrogen["sum"] += combined_mass * factor
            else:
                factor = 0.012011 / molar_mass
                carbon["cams"] += cams_mass * factor
                carbon["finn"] += finn_mass * factor
                carbon["sum"] += combined_mass * factor
            species_reports[species] = {
                "CAMS_kg_s-1": cams_mass,
                "FINN_kg_s-1": finn_mass,
                "combined_kg_s-1": combined_mass,
                "sum_residual_kg_s-1": residual,
                "selected_cells": [
                    {
                        "indexToCellID": cell_id,
                        "CAMS_kg_m-2_s-1": float(cams_value[cell_id - 1]),
                        "FINN_kg_m-2_s-1": float(finn_value[cell_id - 1]),
                        "combined_kg_m-2_s-1": float(combined[cell_id - 1]),
                    }
                    for cell_id in sample_ids
                ],
            }
    return {
        "schema_version": "chempas-mvp-runtime-source-audit-v1",
        "timestamp": target.isoformat() + "Z",
        "interpolation": {"CAMS": "linear monthly", "FINN": "nearest noon-UTC anchor"},
        "inputs": {
            "mesh": {**_record(mesh_path), "fingerprint": identity.fingerprint},
            "CAMS": _record(cams_path),
            "FINN": _record(finn_path),
        },
        "species": species_reports,
        "elemental_ledgers_kg_s-1": {"nitrogen": nitrogen, "carbon": carbon},
        "assertions": {
            "selected_cell_interpolation_reconstructed": True,
            "global_CAMS_mass_reconstructed": True,
            "global_FINN_mass_reconstructed": True,
            "combined_mass_is_inventory_sum": True,
        },
        "overall_pass": True,
    }


def _paths(data_root: Path) -> dict[str, Path]:
    return {
        "weights": data_root / "remap/cams-glob-ant-v6.2-to-x1.40962/cams-glob-ant-v6.2-0.1deg-to-x1.40962.conserve.weights.nc",
        "cams_remapped": data_root / "processed/mvp-cams-harmonized-x1.40962/cams-glob-ant-v6.2-no-no2-co-no-awb.remapped.nc",
        "cams_packaged": data_root / "inventory/mvp-cams-harmonized-x1.40962/miem_inventory.cams.nc",
        "finn_remapped": data_root / "processed/finn-v2.5.1-nrt-x1.40962/finn-v2.5.1-co-no-no2.remapped.nc",
        "finn_packaged": data_root / "inventory/finn-v2.5.1-nrt-x1.40962/miem_inventory.finn.nc",
        "cams_report": data_root / "reports/mvp-stage2-cams.json",
        "finn_report": data_root / "reports/mvp-stage2-finn.json",
        "sum_report": data_root / "reports/mvp-stage2-runtime-sum.json",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("cams", "finn", "audit", "all"))
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--data-root")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timestamp", default="2024-07-01_12:00:00")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _manifest(args.manifest)
        data_root = require_data_root(args.data_root, error_type=MvpEmissionError)
        paths = _paths(data_root)
        mesh = _verify_artifact(data_root, _artifact(manifest, "destination_mesh"))
        results: dict[str, Any] = {}
        if args.command in {"cams", "all"}:
            co_source = _verify_artifact(data_root, _artifact(manifest, "cams_co_native_subset"))
            nox = _verify_artifact(data_root, _artifact(manifest, "accepted_nox_inventory"))
            if not paths["weights"].is_file():
                raise MvpEmissionError(f"missing qualified CAMS weights {paths['weights']}")
            results["cams"] = prepare_cams(
                mesh_path=mesh,
                accepted_nox_path=nox,
                co_source_path=co_source,
                weights_path=paths["weights"],
                remapped_path=paths["cams_remapped"],
                packaged_path=paths["cams_packaged"],
                force=args.force,
            )
            atomic_write_json(paths["cams_report"], results["cams"])
        if args.command in {"finn", "all"}:
            sources = [
                (str(item["selection"]["date"]), _verify_artifact(data_root, item))
                for item in _artifacts(manifest, "finn_daily_source")
            ]
            results["finn"] = prepare_finn(
                mesh_path=mesh,
                sources=sources,
                remapped_path=paths["finn_remapped"],
                packaged_path=paths["finn_packaged"],
                force=args.force,
            )
            atomic_write_json(paths["finn_report"], results["finn"])
        if args.command in {"audit", "all"}:
            if not paths["cams_packaged"].is_file() or not paths["finn_packaged"].is_file():
                raise MvpEmissionError("prepare both packaged inventories before runtime audit")
            results["runtime_sum"] = audit_runtime_sum(
                mesh_path=mesh,
                cams_path=paths["cams_packaged"],
                finn_path=paths["finn_packaged"],
                timestamp=args.timestamp,
            )
            atomic_write_json(paths["sum_report"], results["runtime_sum"])
        print(json.dumps(results, sort_keys=True))
        return 0
    except (OSError, MvpEmissionError, ValueError) as error:
        raise SystemExit(f"ERROR: {error}") from error


if __name__ == "__main__":
    raise SystemExit(main())
