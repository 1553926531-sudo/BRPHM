"""Review frozen inference dependencies without loading any final observations.

Only hash-bound source/configuration/normalization records are read. Selected
pure functions are executed on synthetic inputs; no research module is imported.
The report supplements F1 and does not change the fixed execution protocol.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml


HERE = Path(__file__).absolute().parent
ROOT = HERE.parent.parent
PACKAGE = ROOT / "release/f1_leo900_pre_final_commitment_20261018_r1"
REGISTERED = PACKAGE / "registered_inputs"
SNAPSHOT = HERE / "leo900_preprocess_source_snapshot_20261017T183744Z"
ARCHIVE = ROOT / "release/paper_artifacts_20261018r91/paper_reproduction_20261018r91.tar.gz"
ARCHIVE_SHA = "e8874a5bc8c7e4ced5c0c0e495216497e5d6b5e1d633523d9a0f8167ed4cafb3"
CONTROL_PREFIX = ("revision_20261018r91/audit/f7/host_longrun_20261015/"
                  "work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/")
OUTPUT = HERE / "F1_LEO900_INFERENCE_DEPENDENCIES_20261018R1.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def main():
    require(not OUTPUT.exists(), "append-only report already exists")
    anchors = {}

    def anchor(path, expected):
        raw = path.read_bytes()
        require(digest(raw) == expected, "anchor drift: " + str(path))
        anchors[str(path.relative_to(ROOT)).replace("\\", "/")] = {
            "sha256": expected, "size": len(raw)}
        return json.loads(raw)

    protocol = anchor(HERE / "F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json",
                      "a499b2bbf894a76c2788ed069105f5dd7694160d34f626a5d90f41464586ec3a")
    amendment = anchor(HERE / "F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json",
                       "50e43a0e342799976841da57116bacf09502855f27b116077826bed5b96de8f2")
    closure_path = REGISTERED / "dependency_support_20261018_r3a/F1_LEO900_DEPENDENCY_CLOSURE_20261018R3.json"
    closure = anchor(closure_path, "1507c2b72ad12d7bc1dc080ede4a96b4a8efb216a09d870809c2758386a7cc61")
    candidate = anchor(REGISTERED / "evidence/formal_candidate_receipt.json",
                       "2435584266069cf87cf3333c63633c317af6f9ab55406033d872bfc7b5c608bd")
    require(any(r["path"].endswith("/F1_LEO900_EXECUTION_AMENDMENT_20261018R1.json")
                and r["sha256"] == "50e43a0e342799976841da57116bacf09502855f27b116077826bed5b96de8f2"
                for r in protocol["input_files"]), "amendment parent binding")
    project_records = {r["path"]: r for r in closure["project_files"]}
    execution_records = {r["path"]: r for r in amendment["execution_files"]}
    sources, records, configs, norms = {}, {}, {}, {}

    def add(key, raw, location, binding, parent):
        require(digest(raw) == binding["sha256"] and len(raw) == binding["size"],
                "registered source/configuration drift: " + key)
        text = raw.decode("utf-8")
        sources[key] = text
        records[key] = {"location": location, "sha256": digest(raw), "size": len(raw),
                        "registered_binding": binding, "parent": parent}
        if location.split("::")[-1].endswith(".py"):
            ast.parse(text)

    for key, filename in (("evaluator", "f1_clean_final_test_20261018_v3.py"),
                          ("adapter", "f1_leo900_plain_l1_clean_final_test_20261018_r1.py"),
                          ("trainer", "leo900_source_trainer_20261018/run_l1_mmd_source_only_20261015.py")):
        path = HERE / filename
        add(key, path.read_bytes(), str(path), execution_records[filename], "execution_amendment")
    for key, filename in (("unit_first", "temporal_tcn_unit_first_source_gate_20261001.py"),
                          ("centered", "temporal_tcn_unit_first_residual_centered_source_gate_20261001.py"),
                          ("tcn", "temporal_tcn_source_gate.py"),
                          ("route", "temporal_tcn_global_inner_route_source_gate.py")):
        path = HERE / "source_bindings" / filename
        add(key, path.read_bytes(), str(path),
            project_records["work/rul_next_electrochemical/" + filename], "dependency_closure")
    for name in ("preprocess", "sim_loader", "windows", "labels"):
        rel = "src/datasets/" + name + ".py"
        path = SNAPSHOT / rel
        add(name, path.read_bytes(), str(path), project_records[rel], "dependency_closure")
    for component in ("bat", "rwa"):
        for kind, rel in (("config", f"configs/preprocess/{component}_target.yaml"),
                          ("norm", f"data/processed/norm_stats/{component}_target.json")):
            path = SNAPSHOT / rel
            key = component + "_" + kind
            add(key, path.read_bytes(), str(path), project_records[rel], "dependency_closure")
            if kind == "config":
                configs[component] = yaml.safe_load(sources[key])
            else:
                norms[component] = json.loads(sources[key])
    archive_raw_sha = digest(ARCHIVE.read_bytes())
    require(archive_raw_sha == ARCHIVE_SHA, "reproduction archive drift")
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        for key, name in (("control", "run_segmented_hgb_mlp_source_gate_20260929.py"),
                          ("fixed_mlp", "run_leave_one_orbit_out_generalization_20260825.py"),
                          ("base", "run_component_blend_refinement_20260824.py")):
            member = CONTROL_PREFIX + name
            require(archive.getmember(member).isfile(), "non-file archive member")
            add(key, archive.extractfile(member).read(), str(ARCHIVE) + "::" + member,
                project_records["work/rul_segmented_hgb_mlp_source_gate_20260929/scripts/research/" + name],
                "dependency_closure_and_archive")

    def node(key, name):
        found = [n for n in ast.parse(sources[key]).body
                 if isinstance(n, ast.FunctionDef) and n.name == name]
        require(len(found) == 1, "function missing or ambiguous: " + key + "." + name)
        return found[0]

    def normalized(key, name):
        return ast.unparse(node(key, name))

    def excerpt(key, name):
        n = node(key, name)
        return {"source": key, "function": name, "first_line": n.lineno,
                "last_line": n.end_lineno, "text": "\n".join(sources[key].splitlines()[n.lineno-1:n.end_lineno])}

    def assigned_literal(key, name):
        found = [n.value for n in ast.parse(sources[key]).body
                 if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
        require(len(found) == 1, "literal missing: " + key + "." + name)
        return ast.literal_eval(found[0])

    def synthetic_functions(key, names):
        # Compile only these top-level function bodies. Do not import the module,
        # execute module-level registrations, read data, or construct any model.
        module = ast.Module(body=[node(key, name) for name in names], type_ignores=[])
        env = {"np": np, "Any": Any}
        exec(compile(ast.fix_missing_locations(module), "<synthetic-only:" + key + ">", "exec",
                     flags=__future_annotations_flag(), dont_inherit=True), env)
        return env

    synthetic = []
    rows = [{"unit_id": "synthetic_A", "t_end": 1.0},
            {"unit_id": "synthetic_A", "t_end": 2.0}]
    prediction = np.asarray([0.1, 0.9], dtype=np.float32)
    for key, names in (("tcn", ["project"]), ("base", ["pava", "project"])):
        fn = synthetic_functions(key, names)["project"]
        offline_full = fn(prediction, rows, "isotonic_nonincreasing")
        offline_prefix = fn(prediction[:1], rows[:1], "isotonic_nonincreasing")
        online_full = fn(prediction, rows, "causal_running_min")
        online_prefix = fn(prediction[:1], rows[:1], "causal_running_min")
        require(float(offline_full[0]) != float(offline_prefix[0]), "PAVA future-dependence witness missing")
        require(np.array_equal(online_full[:1], online_prefix), "running-min prefix witness failed")
        synthetic.append({"id": key + "_projection_future_dependency", "input": prediction.tolist(),
                          "isotonic_full": offline_full.tolist(), "isotonic_prefix": offline_prefix.tolist(),
                          "running_min_full": online_full.tolist(), "running_min_prefix": online_prefix.tolist(),
                          "conclusion": "Both registered projection implementations revise the earlier BAT value when a later prediction is appended; their RWA running minima preserve this prefix."})
    functions = synthetic_functions("unit_first", ["_unit_baselines", "append_unit_first"])
    x = np.asarray([[[50.], [51.]], [[10.], [11.]], [[100.], [101.]]], dtype=np.float32)
    unordered = [{"unit_id": "A", "t_end": 4.}, {"unit_id": "A", "t_end": 2.},
                 {"unit_id": "B", "t_end": 2.}]
    baseline = functions["_unit_baselines"](x, unordered)
    require(baseline.tolist() == [[10.], [10.], [100.]], "earliest per-unit baseline witness failed")
    changed = x.copy(); changed[0, 0, 0] = 500.; changed[2, 0, 0] = 900.
    after = functions["_unit_baselines"](changed, unordered)
    require(np.array_equal(after[:2], baseline[:2]), "later-window/cross-unit baseline witness failed")
    synthetic.append({"id": "earliest_window_first_sample", "baseline": baseline.tolist(),
                      "after_later_window_and_other_unit_changes": after.tolist(),
                      "conclusion": "The baseline is the first sample of the smallest-t_end retained window in the same unit, rather than that window's last sample or another unit's input."})

    builder = normalized("evaluator", "build_raw_holdout_payload")
    evaluator = normalized("evaluator", "evaluate")
    adapter = normalized("adapter", "fit_plain_l1_formal")
    prediction_path = normalized("unit_first", "predict_models_unit_first")
    flow = normalized("sim_loader", "to_battery_cycle_frame")
    tcn_cfg = assigned_literal("tcn", "CONFIG")
    control_cfg = assigned_literal("fixed_mlp", "CONFIG")
    facts = []
    created = datetime.now(timezone.utc).isoformat()

    def finding(identity, condition, original, problem, conclusion, refs, risk,
                status="DEPENDENCY_ESTABLISHED_F1_OPEN", extra=None):
        require(condition, identity)
        evidence = [excerpt(*r) for r in refs]
        keys = sorted({r[0] for r in refs})
        facts.append({"id": identity, "位置": [records[k]["location"] for k in keys],
                      "原文": original, "问题": problem,
                      "修改": "追加本条依赖证据；候选、执行链、正文保持冻结。" + conclusion,
                      "证据": {"source_excerpts": evidence, "synthetic_or_configuration": extra},
                      "来源": {k: records[k]["location"] for k in keys}, "日期": created,
                      "哈希": {k: records[k]["sha256"] for k in keys},
                      "命令": "python -B release/f1_audit_20261010/audit_leo900_inference_dependencies_20261018.py",
                      "结果": conclusion,
                      "交叉验证": "逐项比较已登记配置、真实调用函数和父级哈希绑定；纯函数另用合成输入检验。代码副本和哈希不是独立的历史无访问见证。",
                      "置信度": "对所引冻结代码的依赖结论高；不据此证明历史无访问或实测部署可行性。",
                      "剩余风险": risk, "状态": status})

    expected_dims = {"bat": 4, "rwa": 13}
    finding("F1-INFERENCE-01", all(len(configs[c]["channels"]) == expected_dims[c]
            and all(not k.startswith(("label.", "truth/")) for k in configs[c]["channels"]) for c in configs)
            and "for ch in channels" in builder and "frame[ch].to_numpy(np.float64)" in builder,
            "channels = list(config['channels']); matrix = np.column_stack([... for ch in channels])",
            "整个frame含标签和truth衍生量，须核实网络实际取哪些列。",
            "矩阵按冻结通道白名单取值。BAT原始4通道经unit-first拼接为8；RWA原始13通道拼接为26。白名单无label列，但这不等于所有特征都是实测遥测。",
            [("evaluator", "build_raw_holdout_payload"), ("unit_first", "append_unit_first")],
            "特征的生成来源、标签驱动的评估窗口筛选和离线投影仍分别影响可支持的主张。",
            extra={c: {"channels": configs[c]["channels"], "candidate_input_channels": 2*expected_dims[c],
                       "window": configs[c]["window"], "resample": configs[c]["resample"]} for c in configs})
    finding("F1-INFERENCE-02", all(s in flow for s in
            ("sample['tru']['soh']", "cap = q0 * soh_s", "'bat.capacity_ah': _f32(cap)", "hit = np.nonzero(cap <= thr + 1e-09)[0]")),
            "soh_s = sample['tru']['soh'][settle]; cap = q0 * soh_s; ft_cyc = hit[0]",
            "BAT容量输入和失效标签共享模拟SOH状态，不能统称为在线实测传感器。",
            "BAT容量是从仿真truth/soh重建的理想容量代理；标签失效循环也从容量阈值确定。这不是直接把RUL列喂给网络，但部署可测性、噪声和与标签的结构关系须披露并另行验证。",
            [("sim_loader", "to_battery_cycle_frame"), ("evaluator", "build_raw_holdout_payload")],
            "未检验真实容量估计误差或在轨可用性；不得据此声称真实硬件部署已经成立。")
    finding("F1-INFERENCE-03", "lab = {'rul_days': _vec(f, 'labels/rul_days')" in normalized("sim_loader", "read_simout")
            and "sample = read_simout(path, lenient=lenient)" in normalized("sim_loader", "convert_one"),
            "convert_one -> read_simout loads telemetry, truth, labels and failure_time_days",
            "一次性评估的读入层事实上会读完整的标签与真值结构。",
            "最终evaluate在独占访问guard之后转换MAT；转换器读取标签、失效时间和truth以校验契约和构造评估数据。因此全pipeline从不读目标标签这一说法不成立。它与训练不以final标签拟合是不同结论。",
            [("evaluator", "evaluate"), ("sim_loader", "convert_one"), ("sim_loader", "read_simout")],
            "需终态收据证明读取发生在freeze之后；静态审查不能证明历史没有其他读取者。")
    finding("F1-INFERENCE-04", "keep = np.isfinite(y)" in builder and "keep &= y >= 0.0" in builder
            and all(configs[c]["labels"]["rul_floor"] == "drop_negative" for c in configs),
            "keep = np.isfinite(y); keep &= y >= 0.0; windows_array, ends, y = ...[keep]",
            "最终评估成员关系依赖目标标签有效性与失效后尾部剔除。",
            "标签先按窗末取值并封顶，再剔除非有限或负标签窗口；筛选发生在预测之前。网络拟合虽不使用final标签，后续unit baseline和投影的输入成员关系依赖这份固定评估筛选。只能在给定该评估成员关系时讨论label-free预测算子。",
            [("evaluator", "build_raw_holdout_payload"), ("labels", "cap_rul"), ("labels", "window_labels")],
            "删失unit或短unit可零窗口；最终96个生成unit不自动等于96个有评估窗口的unit。必须读取终态per-unit counts核对，不能提前保证。",
            extra={c: configs[c]["labels"] for c in configs})
    finding("F1-INFERENCE-05", "t_end < first[key][0]" in normalized("unit_first", "_unit_baselines")
            and "values[first[str(row['unit_id'])][1], 0, :]" in normalized("unit_first", "_unit_baselines")
            and "append_unit_first(normalized, rows)" in prediction_path,
            "baseline[index] = values[first[unit_id][1], 0, :]",
            "unit-first需要目标unit的历史输入，须明确最早窗口和样本位置。",
            "每个目标unit从保留窗口中取最小t_end窗口的第一个sample作baseline。可在首个完整窗口可用后取得；不估计目标总体均值，不使用该窗口的RUL数值。baseline依赖既定评估成员关系。",
            [("unit_first", "_unit_baselines"), ("unit_first", "append_unit_first"), ("unit_first", "predict_models_unit_first")],
            "不能把需要目标unit历史输入的路径写成仅凭source输入完成；输入缺失或评估筛选变化需新的预定义处理。",
            extra=synthetic[2])
    finding("F1-INFERENCE-06", all(s in adapter for s in
            ("source_x = data['x'][train]", "center = source_x.mean", "scale = np.maximum(source_x.std"))
            and "baseline_coef" in builder and "preprocess.normalize(windows_array, channels, stats)" in builder
            and "for row in train_rows" in normalized("control", "fit_predict_fixed"),
            "source mean/std; frozen norm_doc baseline_coef; tmax from train_rows",
            "需排除以目标总体统计量重新归一化或拟合摩擦基线。",
            "最终raw转换使用已冻结的归一化和RWA摩擦基线；TCN的第二层标准化仅取source_x，年龄分母仅取训练rows。固定源码未在final样本上重新拟合这些参数。",
            [("evaluator", "build_raw_holdout_payload"), ("adapter", "fit_plain_l1_formal"),
             ("preprocess", "normalize"), ("tcn", "_age"), ("control", "fit_predict_fixed")],
            "norm_doc的旧训练来源仍须保留其原始split provenance；这不追溯证明旧source gate的全部历史独立性。",
            extra={c: {"computed_on": norms[c]["computed_on"], "created_utc": norms[c]["created_utc"],
                       "derived": norms[c]["derived"]} for c in norms})
    finding("F1-INFERENCE-07", "str(row['unit_id']).split('_')[1]" in evaluator
            and all(candidate["components"][c]["selected_route"]["alpha_by_target"]["LEO900"] == 1e-5 for c in configs),
            "alpha_by_target[str(row['unit_id']).split('_')[1]]",
            "该执行入口需要已知轨道身份，不能声称轨道未知时也自动选择。",
            "最终alpha按unit_id中的已知轨道名查固定映射；LEO900两个组件均固定1e-5。目标标签或预测误差未用于这一运行时查表。未知或未登记轨道缺少键会报错，不存在自动学习该轨道alpha的机制。",
            [("evaluator", "evaluate"), ("route", "reference_control_candidate")],
            "旧outer与LEO800反馈影响过开发过程；本次冻结查表不能把整个方法历史改称source-only。",
            extra={c: candidate["components"][c]["selected_route"] for c in configs})
    finding("F1-INFERENCE-08", tcn_cfg["bat"]["postprocess"] == control_cfg["bat"]["postprocess"] == "isotonic_nonincreasing"
            and tcn_cfg["rwa"]["postprocess"] == control_cfg["rwa"]["postprocess"] == "causal_running_min",
            "BAT: isotonic_nonincreasing; RWA: causal_running_min",
            "单窗模型与跨窗口投影的时间因果性必须分开审计。",
            "BAT candidate、control及最终blend均采用整unit离线PAVA，后期输入可修订早期输出。两个注册实现的合成反例均为prefix[0.1]→0.1、追加0.9后早值→0.5。RWA running-min算子在相同prefix与成员关系下为因果；这不等于完整评估管线已证明在线。",
            [("tcn", "project"), ("base", "pava"), ("base", "project"), ("evaluator", "evaluate")],
            "尚无单独冻结并执行的严格在线BAT结果；不能以离线结果代替该结果。",
            extra={"tcn_config": tcn_cfg, "control_config": control_cfg, "synthetic": synthetic[:2]})
    finding("F1-INFERENCE-09", "centered.b.project(valid_raw + np.float32(correction)" in adapter
            and "projected = base.project(segmented(" in normalized("control", "fit_predict_fixed")
            and evaluator.index("blended = alpha *") < evaluator.index("prediction = centered.b.project"),
            "candidate projection; control projection; alpha blend; final projection; metrics",
            "收据中的final unit projection applied once容易被误读为全流程只投影一次。",
            "准确顺序为：source标准化→unit-first拼接→固定epoch ensemble→source残差校正→candidate投影；control经分段混合及独立投影；再按alpha混合两分支，并对blend再投影，然后计算指标。一次只指最后这一层，不能省略分支投影。",
            [("adapter", "fit_plain_l1_formal"), ("control", "fit_predict_fixed"), ("evaluator", "evaluate")],
            "真实执行的输入输出哈希、投影前后预测与终态链仍待独立核验；本报告不执行模型。")
    finding("F1-INFERENCE-10", configs["rwa"]["resample"]["bin_s"] == 574.0
            and "g[ch].agg(['mean', 'std', 'min', 'max'])" in normalized("preprocess", "_bin_aggregate_rwa")
            and "last_cols" in normalized("preprocess", "_bin_aggregate_rwa"),
            "resample.mode=daily_agg, bin_s=574.0; window L=30,stride=1",
            "daily_agg函数名称不等于本实验按一天聚合；单位与特征时点可能被误报。",
            "RWA本配置按574秒bin聚合三路遥测的mean/std/min/max，加冻结温度基线残差共13通道；窗口30bin，步长1bin。t取每组末尾原始时间，单位day。标签列单独carry并用于评估，未进入三路遥测聚合。",
            [("preprocess", "_bin_aggregate_rwa"), ("evaluator", "build_raw_holdout_payload"),
             ("windows", "slide"), ("windows", "build_index")],
            "bin内特征在该bin结束后才可用；singleton的std可能非有限，注册R4在冻结归一化后插补0，未以final统计量拟合。",
            extra={"bin_seconds": 574.0, "window_bins": 30, "stride_bins": 1, "rul_unit": "day"})

    fields = {"位置", "原文", "问题", "修改", "证据", "来源", "日期", "哈希", "命令", "结果", "交叉验证", "置信度", "剩余风险", "状态"}
    require(all(fields <= set(f) for f in facts) and len({f["id"] for f in facts}) == len(facts), "finding schema")
    report = {
        "schema": "brphm-f1-frozen-inference-dependency-audit-v1", "created_utc": created,
        "status": "DEPENDENCIES_ESTABLISHED_F1_OPEN", "f1_closed": False,
        "scientific_success_claimed": False, "goal_must_remain_active": True,
        "script_sha256": digest(Path(__file__).read_bytes()), "anchors": anchors,
        "archive": {"path": str(ARCHIVE), "sha256": archive_raw_sha},
        "sources": records, "findings": facts, "synthetic_witnesses": synthetic,
        "interpretation": {
            "fixed_final_training_uses_target_labels": "No use in the audited fitting path; terminal runtime evidence still required.",
            "entire_pipeline_never_reads_target_labels": False,
            "prediction_membership_independent_of_target_labels": False,
            "bat_strictly_online_result_established": False,
            "rwa_projection_operator_prefix_causal": True,
            "known_orbit_identity_required_by_entrypoint": True,
            "unlabeled_target_unit_history_used": True,
            "target_population_statistics_refitted": "Not present in audited frozen inference path.",
            "bat_capacity_input_source": "simulation truth/soh; ideal capacity proxy",
            "new_final_population_generalization_or_practical_superiority_established": False,
        },
        "read_scope": {"actual_mat_or_final_tensor_or_prediction_arrays_read": False,
                       "real_final_labels_or_telemetry_decoded": False,
                       "research_modules_imported": False,
                       "selected_pure_functions_executed_on_synthetic_inputs": True,
                       "training_or_final_evaluation_invoked": False,
                       "remote_access_or_mutation": False,
                       "frozen_candidate_or_protocol_modified": False,
                       "manuscript_or_F2_F10_modified": False},
        "limitations": ["Static review and synthetic witnesses are not a whole-program information-flow proof.",
                        "Registered copies and hashes are not independent evidence of historical non-access.",
                        "The final result and all generated-unit/retained-unit counts must be checked after the guarded execution.",
                        "No result-driven modification or repeated evaluation on LEO900 is authorized by this report."]}
    with OUTPUT.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"output": str(OUTPUT), "sha256": digest(OUTPUT.read_bytes()),
                      "status": report["status"], "sources": len(records), "findings": len(facts),
                      "synthetic_witnesses": len(synthetic)}))


def __future_annotations_flag():
    import __future__
    return __future__.annotations.compiler_flag


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
