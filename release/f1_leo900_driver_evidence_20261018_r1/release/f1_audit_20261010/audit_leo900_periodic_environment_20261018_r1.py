"""Append a read-only, pre-outcome analysis of the frozen periodic driver.

This program reads captured logs/source/model XML only. It neither connects to
Rack nor changes any execution, candidate, scientific gate or manuscript.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = {
    "leo900_environment_diagnostic_observation_20261018T003316Z.json": "3679f56ee1de5648b98aeeca2d3b519951a22778e4a77594be56079396c39573",
    "leo900_environment_consumer_observation_20261018T003440Z.json": "b37f15701225a93d94792d951e05bdb3084aa44f4ef5bcbd65d35b02ae0e189d",
    "leo900_environment_slx_observation_20261018T003634Z.json": "e77ed352d74c682d2a26090e47537b83fe579e4337dba691e3d2c7068f49331c",
    "leo900_generation_manifest_20261017.json": "3c2480f15f8244dc8f645696f8fe5616a09d4f2efd8f904a1777bef2992cba52",
    "leo900_import_validation_20261017.json": "2181fd745d824e212c2ad904af0fac44abfe816fbbbc90b290e6c90ad0cea67a",
    "leo900_combined_execution_observation_20261018T003357Z.json": "98380be0b76ea6c1b8c763f0cb84ce6324ad1176ba7e511e8d280eaee8659f3d",
    "F1_LEO900_GENERATOR_STATIC_EVIDENCE_20261018R2.json": "43349e22cea2d1bf140b7b7145879628c9d6a9e40cfa8b1e16f1a9198f1fd64a",
    "leo900_generator_code_observation_20261018T001654Z.json": "91a79136c1efab72ba8a02585c59a762fa738d3be77870acaf7a1bfbeb8aa1a4",
}
OUT = HERE / "F1_LEO900_PERIODIC_DRIVER_EVIDENCE_20261018R1.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name):
    raw = (HERE / name).read_bytes()
    assert digest(raw) == INPUTS[name], name
    return json.loads(raw)


def graph(member):
    raw = member["text_utf8"].encode("utf-8")
    assert digest(raw) == member["sha256"]
    system = ET.fromstring(raw)
    blocks = {b.attrib["SID"]: b for b in system.findall("Block")}
    names = {sid: b.attrib["Name"] for sid, b in blocks.items()}
    edges = []
    for line in system.findall("Line"):
        source = line.find("P[@Name='Src']")
        if source is None:
            continue
        sid, port = source.text.split("#", 1)
        for destination in line.findall(".//P[@Name='Dst']"):
            other, other_port = destination.text.split("#", 1)
            edges.append((names[sid], port, names[other], other_port))
    return blocks, edges


def main():
    assert not OUT.exists() and not OUT.with_suffix(".md").exists(), "preserve prior evidence"
    docs = {name: load(name) for name in INPUTS}
    observation = docs["leo900_environment_diagnostic_observation_20261018T003316Z.json"]
    generation = docs["leo900_generation_manifest_20261017.json"]
    capture = docs["leo900_environment_slx_observation_20261018T003634Z.json"]
    live = docs["leo900_combined_execution_observation_20261018T003357Z.json"]
    assert not live["controller"]["documents"]["guard"]["exists"]
    assert observation["stat_before"] == observation["stat_after"]
    assert len(observation["diagnostic_rows"]) == 3
    assert {r["id"] for r in generation["cases"]} == {"LEO900_B00", "LEO900_B30", "LEO900_B60"}
    axes = {r["semi_major_axis_km"] for r in generation["cases"]}
    assert len(axes) == 1
    a = axes.pop()
    mu, period = 398600.4418, 5740.0
    reference = 2 * math.pi * math.sqrt(a**3 / mu)
    rows = []
    pattern = re.compile(
        r"^\[env\]\s+(LEO900_B\d+)\s+tile@t0=(\d+)\s*s \| "
        r"T_orb\u2248(\d+) s \(P=(\d+), \u5dee ([+-]\d+) s\) \| "
        r"\u5f71 (\d+) \u62cd duty ([\d.]+)% \| \u7f1d\u8df3 (\d+) km \| "
        r"\u03b2=([+-][\d.]+)\u00b0 \| i_chg=([+-]?[\d.]+) A$"
    )
    for record in observation["diagnostic_rows"]:
        match = pattern.fullmatch(record["text_utf8"])
        assert match, record
        case, t0, orbital, tile, difference, n2, duty, seam, beta, current = match.groups()
        tile, n2 = int(tile), int(n2)
        assert tile == period and tile % 10 == 0
        samples = tile // 10
        charge = -2.0 * n2 / (samples - n2)
        assert f"{100*n2/samples:.1f}" == duty and f"{charge:.3f}" == current
        rows.append(dict(
            case=case, log_line=record["line_number"], tile_start_s=int(t0),
            logged_orbital_period_rounded_s=int(orbital), tile_period_s=tile,
            logged_period_difference_rounded_s=int(difference),
            logged_seam_rounded_km=int(seam), umbra_samples=n2,
            umbra_duration_on_ten_second_grid_s=10*n2,
            duty_percent_recomputed=100*n2/samples,
            logged_beta_rounded_deg=float(beta),
            charge_current_recomputed_a=charge,
            duty_precision="one decimal percent in log",
            orbital_and_seam_precision="rounded whole seconds and kilometres in log",
        ))
    bindings = []
    for name, model in capture["models"].items():
        assert model["exists"] and model["matches_registry"], name
        for member in model["selected_xml_members"]:
            blocks, edges = graph(member)
            if name != "sim/model/satellite_top.slx":
                continue
            if member["name"].endswith("system_root.xml"):
                required = [
                    ("fw_r", "out:1", "thermal_net", "in:2"),
                    ("fw_sun", "out:1", "thermal_net", "in:1"),
                    ("fw_flag", "out:1", "thermal_net", "in:3"),
                    ("fw_flag", "out:1", "lut_iload", "in:1"),
                    ("thermal_net", "out:1", "rw_assembly", "in:2"),
                    ("thermal_net", "out:2", "power_ecm", "in:2"),
                ]
            else:
                chain = ["r_eci_km", "dot_sr", "div_cos", "max_cos", "g_qzen", "sum_qfull", "prod_qsol", "sum_str", "g_invCstr", "int_str"]
                assert all(any(e[0] == x and e[2] == y for e in edges) for x, y in zip(chain, chain[1:]))
                required = [edge for edge in edges if any(edge[0] == x and edge[2] == y for x, y in zip(chain, chain[1:]))]
            assert set(required) <= set(edges), member["name"]
            bindings.append(dict(model=name, member=member["name"], member_sha256=member["sha256"], verified_edges=required))
    assert len(bindings) == 2
    calculated = dict(
        semimajor_axis_km=a, gravitational_parameter_km3_s2=mu,
        formula="T=2*pi*sqrt(a**3/mu)", semimajor_period_s=reference,
        tile_minus_reference_period_s=period-reference,
        fractional_period_shortening=(reference-period)/reference,
        relative_repeat_rate_increase=reference/period-1,
        circular_reference_phase_gap_deg=360*(reference-period)/reference,
        circular_reference_chord_km=2*a*math.sin(math.pi*(reference-period)/reference),
        approximation_scope="The phase/chord quantities are circular-reference checks. The generator uses eccentricity 0.001, interpolation and a tile-mean-radius period; these calculations are not a substitute for runtime diagnostics or a dynamical sensitivity simulation.",
    )
    now = datetime.now(timezone.utc).isoformat()
    previous = docs["F1_LEO900_GENERATOR_STATIC_EVIDENCE_20261018R2.json"]
    fields = dict(
        location="Original review F1 lines19-25; make_dataset.m:119,562-567,1080-1120; captured satellite_top.slx environment/thermal bindings. Evidence only; no manuscript revision.",
        original=previous["fields"]["original"],
        problem="The newly generated LEO900 cohort uses a frozen periodic environmental approximation. An import PASS alone does not describe the actual repeated driver or establish physical fidelity. Its scientific interpretation must be examined alongside the final-test provenance.",
        modification="Append this pre-outcome analysis and its read-only captures. Keep the simulation, configuration, candidate, controller, watcher, scientific gates, final access policy and manuscript unchanged. No new acceptance threshold is introduced.",
        evidence=list(INPUTS),
        source="Captured generation stdout, preparation-bound generator/builders and actual registered SLX XML, analytic environment manifest, and earlier import validation. Source code and serialized model are separate representations from one pipeline. The Kepler calculation is a local mathematical cross-check, not an independent simulator or outside attestation.",
        date=now,
        hash={"input_sha256":INPUTS,"analysis_program_sha256":digest(Path(__file__).read_bytes()),"models":{name:row["sha256"] for name,row in capture["models"].items()}},
        command="python -B release/f1_audit_20261010/audit_leo900_periodic_environment_20261018_r1.py ; exact SSH read-only capture code is embedded in each observation. The first source-search attempt found no rg executable on Rack; the retained successful capture uses pathlib/regex instead, without installing software or changing execution.",
        result="All three logs use P5740s against rounded tile-mean-radius periods6179-6180s and report positional seams3222-3228km. The semimajor-axis calculation gives6179.328127714831s:7.10964232089255% shorter repetition period and7.65380013440471% higher repetition rate. The circular-reference seam3224.265337627792km corroborates the scale. Logged umbra duties and charge currents are reproduced at their printed precision. Registered model XML confirms the geometry-to-solar-heat path and thermal connections to both components. No RUL error, temperature response or performance effect has been measured by this analysis.",
        cross_validation="Generator source fixes5740s and repeats574 samples; separate runtime diagnostics quantify the same driver. The declared7278.1363km semimajor axis with the declared Earth mu predicts the observed period and seam scale. Build source and separately captured, hash-matched SLX XML agree on environmental/thermal connections. Charging/duty arithmetic is independently recalculated from logged grid counts. These checks corroborate implementation; they are not independent physical validation or a proof of absent prior final access.",
        confidence="High for captured bytes, reported driver diagnostics, arithmetic and static model bindings. No confidence claim for the size or sign of an unmeasured prediction/temperature effect.",
        remaining_risk="Repeated geometry is not a continuously propagated30-day orbit. Its shorter cycle and position seam can change thermal forcing and the timing of eclipses/charging; their effect on temperatures, component lifetimes and model comparisons remains unmeasured. XML on disk is not an observation of every loaded MATLAB runtime state. The log periods/seams are rounded. No new arbitrary validity cutoff or post-result outcome-selection rule is introduced. This record neither establishes model superiority nor closes F1; the registered terminal chain, actual cohort/subset, single-access chronology, effects and uncertainty still require review. A new final cannot retroactively restore confirmatory status to reused historical outer folds.",
        status="PERIODIC DRIVER APPROXIMATION QUANTIFIED BEFORE OBSERVED FINAL ACCESS; OUTCOME SENSITIVITY UNMEASURED; F1 OPEN",
    )
    doc = dict(
        schema="brphm-f1-leo900-periodic-driver-evidence-v1",created_utc=now,
        finding="F1",fields=fields,driver_diagnostics=rows,
        mathematical_cross_check=calculated,static_model_bindings=bindings,
        final_guard_absent_at_observed_utc=live["controller"]["observed_utc"],
        final_guard_absence_scope="Point-in-time observation only; no claim of global historical non-access.",
        f1_closed=False,goal_status="active",scientific_success_claimed=False,
        manuscript_and_f2_f10_substantive_edits_frozen=True,
        simulation_or_candidate_modified=False,remote_writes=False,
        semantic_final_labels_read=False,
    )
    encoded = (json.dumps(doc,ensure_ascii=True,indent=2,sort_keys=True,allow_nan=False)+"\n").encode("utf-8")
    table = "\n".join(f"| {r['case']} | {r['logged_orbital_period_rounded_s']} | {r['tile_period_s']} | {r['logged_seam_rounded_km']} | {r['duty_percent_recomputed']:.9f} | {r['charge_current_recomputed_a']:.12f} |" for r in rows)
    markdown = f"""# F1 LEO900 periodic-driver evidence

F1 remains OPEN; the F1-F10 goal remains active. This is a pre-outcome evidence addition, with no change to the frozen simulation, candidate, gates, access policy or manuscript.

The declared analytic orbit has a reference Kepler period of {reference:.12f} s. The actual frozen generator repeats a5740s tile. The period is7.109642321% shorter, giving7.653800134% more repetitions per unit time. These are driver quantities, not prediction improvements. A circular-reference seam is3224.265338km; runtime diagnostics report3222-3228km. The circular calculation does not reproduce a full eccentric/interpolated orbit.

| Environment | Logged period, rounded s | Tile s | Logged seam, rounded km | Recomputed umbra duty % | Recomputed charging A |
|---|---:|---:|---:|---:|---:|
{table}

The registered serialized model and build source both connect the environmental position to solar heat and the thermal model to BAT and RWA. Therefore the seam has a possible physical influence. No sensitivity simulation, final RUL labels or model outcomes were inspected; this record does not estimate that influence or declare the experiment valid/invalid by a new threshold. The import PASS is not evidence that a30-day continuous orbit drove the model.

The accompanying JSON contains all14 finding fields, exact input hashes, formulas and verified model edges. Read-only capture programs are embedded in the referenced observations. This analysis can be reviewed or rerun in a disposable copy; its output writer refuses to overwrite existing evidence. The original run and registered terminal auditors continue automatically.

JSON SHA256: `{digest(encoded)}`. Created UTC: {now}.
"""
    with OUT.open("xb") as handle:
        handle.write(encoded)
    with OUT.with_suffix(".md").open("xb") as handle:
        handle.write(markdown.encode("utf-8"))
    print(json.dumps(dict(output=str(OUT),sha256=digest(encoded),markdown_sha256=digest(markdown.encode("utf-8")),environment_cases=len(rows),verified_xml_members=len(bindings),f1_closed=False)))


if __name__ == "__main__":
    main()
