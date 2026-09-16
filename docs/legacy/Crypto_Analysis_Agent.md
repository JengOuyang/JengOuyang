# 舊專案盤點：戰情室與行動端（`Crypto_Analysis_Agent`）

> 由 `python scripts/scan_legacy.py` 自動生成，**不要手改表格**——只有「決定」欄是給你填的。

- 路徑：`C:\Users\Ouyang\Desktop\My AI Agent\Crypto Analysis Agent`
- 狀態：production　信任度：medium
- 檔案數：46088

## 已驗證的事實（CEO 派工時的優先依據）

- 每日盤面分析串接Canva
- 以DNN架構做盤面分析

## 踩過的坑（比程式本身更值錢——移植時必須保留這些處理）

- 無法直接推送Instegram
- 盤面分析不準確

## ⚠️ 含疑似金鑰的檔案（移植前必須先清掉，並在交易所端輪換）

- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/git/remote.py`
- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/numpy/distutils/mingw32ccompiler.py`
- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/plotly/io/_orca.py`
- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/pyarrow/tests/test_flight.py`
- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/pyarrow/tests/test_fs.py`
- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/hub.py`
- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/tornado/test/auth_test.py`
- `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/tornado/test/web_test.py`
- `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/git/remote.py`
- `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/plotly/io/_orca.py`
- `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/pyarrow/tests/test_flight.py`
- `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/pyarrow/tests/test_fs.py`
- `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/hub.py`
- `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/tornado/test/auth_test.py`
- `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/tornado/test/web_test.py`
- `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/git/remote.py`
- `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/plotly/io/_orca.py`
- `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/pyarrow/tests/test_flight.py`
- `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/pyarrow/tests/test_fs.py`
- `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/hub.py`
- `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/tornado/test/auth_test.py`
- `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/tornado/test/web_test.py`
- `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/git/remote.py`
- `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/plotly/io/_orca.py`
- `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/pyarrow/tests/test_flight.py`
- `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/pyarrow/tests/test_fs.py`
- `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/hub.py`
- `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/tornado/test/auth_test.py`
- `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/tornado/test/web_test.py`

## 依能力分類

### _未分類

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/scipy/stats/_continuous_distns.py` | 12544 | _censored_data, _constants, _distn_infrastructure, _ksstats, _tukeylambda_stats | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/scipy/stats/_continuous_distns.py` | 12544 | _censored_data, _constants, _distn_infrastructure, _ksstats, _tukeylambda_stats | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/scipy/stats/_continuous_distns.py` | 12544 | _censored_data, _constants, _distn_infrastructure, _ksstats, _tukeylambda_stats | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/scipy/stats/_continuous_distns.py` | 12544 | _censored_data, _constants, _distn_infrastructure, _ksstats, _tukeylambda_stats | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/testing/_internal/distributed/distributed_test.py` | 10495 | collections, contextlib, copy, dataclasses, datetime | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/testing/_internal/distributed/distributed_test.py` | 10495 | collections, contextlib, copy, dataclasses, datetime | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/testing/_internal/distributed/distributed_test.py` | 10495 | collections, contextlib, copy, dataclasses, datetime | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/testing/_internal/distributed/distributed_test.py` | 10495 | collections, contextlib, copy, dataclasses, datetime | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/mpmath/function_docs.py` | 10202 | — | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/mpmath/function_docs.py` | 10202 | — | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/mpmath/function_docs.py` | 10202 | — | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/mpmath/function_docs.py` | 10202 | — | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/_inductor/ir.py` | 9967 | __future__, codegen, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/_inductor/ir.py` | 9967 | __future__, codegen, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/_inductor/ir.py` | 9967 | __future__, codegen, collections, contextlib, copy | |

### backtest-walkforward

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/backtest/results_20260430T045434Z.json` | 19534 | — | |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140146Z.json` | 19534 | — | |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140353Z.json` | 19390 | — | |
| `Crypto Analysis/m5_backtest/m4_backtest.py` | 1073 | argparse, collections, concurrent, datetime, json | |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140530Z.json` | 920 | — | |
| `Crypto Analysis/system_guide.html` | 904 | — | |
| `Crypto Analysis/m5_backtest/engine.py` | 794 | collections, datetime, m2_analyzer, numpy, os | |
| `Crypto Analysis/m5_backtest/train_m35.py` | 649 | argparse, data, datetime, json, m3_5_dnn | |
| `Crypto Analysis/m3_5_dnn/model.py` | 549 | features, logging, numpy, os, pickle | |
| `Crypto Analysis/m5_backtest/backtest/results_20260505T140401Z.json` | 487 | — | |
| `Crypto Analysis/m5_backtest/promotion_gate.py` | 409 | __future__, datetime, json, m5_backtest, numpy | |
| `Crypto Analysis/m5_backtest/collect_m4_training_data.py` | 376 | __future__, argparse, datetime, m3_5_dnn, m3_signals | |
| `Crypto Analysis/tests/test_e2e.py` | 353 | data, m1_5_daily, m3_5_dnn, m3_signals, m4_risk | |
| `Crypto Analysis/CLAUDE.md` | 346 | — | |
| `Crypto Analysis/dev_tool/tune/m4_lab.py` | 332 | __future__, copy, dataclasses, dev_tool, json | |

### canva-content

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/networkx/drawing/nx_pylab.py` | 2979 | collections, inspect, itertools, math, matplotlib | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/networkx/drawing/nx_pylab.py` | 2979 | collections, inspect, itertools, math, matplotlib | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/networkx/drawing/nx_pylab.py` | 2979 | collections, inspect, itertools, math, matplotlib | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/networkx/drawing/nx_pylab.py` | 2979 | collections, inspect, itertools, math, matplotlib | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/networkx/drawing/tests/test_pylab.py` | 1583 | itertools, matplotlib, networkx, os, pytest | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/networkx/drawing/tests/test_pylab.py` | 1583 | itertools, matplotlib, networkx, os, pytest | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/networkx/drawing/tests/test_pylab.py` | 1583 | itertools, matplotlib, networkx, os, pytest | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/networkx/drawing/tests/test_pylab.py` | 1583 | itertools, matplotlib, networkx, os, pytest | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/sympy/plotting/plot.py` | 1235 | sympy | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/sympy/plotting/plot.py` | 1235 | sympy | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/sympy/plotting/plot.py` | 1235 | sympy | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/sympy/plotting/plot.py` | 1235 | sympy | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/utils/tensorboard/writer.py` | 1220 | _convert_np, _embedding, _onnx_graph, _pytorch_graph, _utils | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/utils/tensorboard/writer.py` | 1220 | _convert_np, _embedding, _onnx_graph, _pytorch_graph, _utils | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/utils/tensorboard/writer.py` | 1220 | _convert_np, _embedding, _onnx_graph, _pytorch_graph, _utils | |

### data-integrity

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/pandas/core/generic.py` | 14026 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/pandas/core/generic.py` | 14026 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/pandas/core/generic.py` | 14026 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/pandas/core/generic.py` | 14026 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/pandas/core/frame.py` | 12725 | __future__, collections, datetime, functools, inspect | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/pandas/core/frame.py` | 12725 | __future__, collections, datetime, functools, inspect | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/pandas/core/frame.py` | 12725 | __future__, collections, datetime, functools, inspect | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/pandas/core/frame.py` | 12725 | __future__, collections, datetime, functools, inspect | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/fx/experimental/symbolic_shapes.py` | 8364 | __future__, abc, atexit, bisect, collections | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/fx/experimental/symbolic_shapes.py` | 8364 | __future__, abc, atexit, bisect, collections | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/fx/experimental/symbolic_shapes.py` | 8364 | __future__, abc, atexit, bisect, collections | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/fx/experimental/symbolic_shapes.py` | 8364 | __future__, abc, atexit, bisect, collections | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/testing/_internal/common_utils.py` | 6047 | __main__, argparse, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/testing/_internal/common_utils.py` | 6047 | __main__, argparse, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/testing/_internal/common_utils.py` | 6047 | __main__, argparse, collections, contextlib, copy | |

### exchange-position-guard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torchgen/packaged/ATen/native/native_functions.yaml` | 16173 | inheriting | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torchgen/packaged/ATen/native/native_functions.yaml` | 16173 | inheriting | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torchgen/packaged/ATen/native/native_functions.yaml` | 16173 | inheriting | |

### exchange-reconciliation

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/pandas/core/indexes/base.py` | 7944 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/pandas/core/indexes/base.py` | 7944 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/pandas/core/indexes/base.py` | 7944 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/pandas/core/indexes/base.py` | 7944 | __future__, collections, copy, datetime, functools | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/_dynamo/guards.py` | 4892 | __future__, ast, builtins, collections, contextlib | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/_dynamo/guards.py` | 4892 | __future__, ast, builtins, collections, contextlib | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/_dynamo/guards.py` | 4892 | __future__, ast, builtins, collections, contextlib | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/_dynamo/guards.py` | 4892 | __future__, ast, builtins, collections, contextlib | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/_dynamo/trace_rules.py` | 4081 | abc, builtins, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/_dynamo/trace_rules.py` | 4081 | abc, builtins, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/_dynamo/trace_rules.py` | 4081 | abc, builtins, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/_dynamo/trace_rules.py` | 4081 | abc, builtins, collections, contextlib, copy | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/narwhals/series.py` | 2951 | __future__, collections, functools, math, narwhals | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/narwhals/series.py` | 2951 | __future__, collections, functools, math, narwhals | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/narwhals/series.py` | 2951 | __future__, collections, functools, math, narwhals | |

### macro-briefing

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/pip/_vendor/pyparsing/core.py` | 6116 | abc, actions, collections, copy, diagram | |
| `Crypto Analysis/dev_sandboxvenv_py311/Lib/site-packages/pip/_vendor/pyparsing/core.py` | 6116 | abc, actions, collections, copy, diagram | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/pkg_resources/_vendor/pyparsing/core.py` | 5815 | abc, actions, collections, copy, diagram | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/setuptools/_vendor/pyparsing/core.py` | 5815 | abc, actions, collections, copy, diagram | |
| `Crypto Analysis/dev_sandboxvenv_py311/Lib/site-packages/pkg_resources/_vendor/pyparsing/core.py` | 5815 | abc, actions, collections, copy, diagram | |
| `Crypto Analysis/dev_sandboxvenv_py311/Lib/site-packages/setuptools/_vendor/pyparsing/core.py` | 5815 | abc, actions, collections, copy, diagram | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/scipy/signal/_signaltools.py` | 5357 | __future__, _arraytools, _filter_design, _fir_filter_design, _ltisys | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/scipy/signal/_signaltools.py` | 5357 | __future__, _arraytools, _filter_design, _fir_filter_design, _ltisys | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/scipy/signal/_signaltools.py` | 5357 | __future__, _arraytools, _filter_design, _fir_filter_design, _ltisys | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/scipy/signal/_signaltools.py` | 5357 | __future__, _arraytools, _filter_design, _fir_filter_design, _ltisys | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/pygments/lexers/_lasso_builtins.py` | 5327 | — | |

### market-data-collection

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/plotly/graph_objs/_figure.py` | 25395 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/numpy/_core/_add_newdocs.py` | 7162 | numpy, textwrap | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/numpy/_core/_add_newdocs.py` | 7162 | numpy, textwrap | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/numpy/_core/_add_newdocs.py` | 7162 | numpy, textwrap | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/numpy/_core/_add_newdocs.py` | 7162 | numpy, textwrap | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/scipy/cluster/hierarchy.py` | 4339 | bisect, collections, matplotlib, numpy, scipy | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/scipy/cluster/hierarchy.py` | 4339 | bisect, collections, matplotlib, numpy, scipy | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/scipy/cluster/hierarchy.py` | 4339 | bisect, collections, matplotlib, numpy, scipy | |

### pattern-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/altair/vegalite/v5/schema/vega-lite-schema.json` | 32223 | — | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/altair/vegalite/v5/schema/vega-lite-schema.json` | 32223 | — | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/altair/vegalite/v5/schema/vega-lite-schema.json` | 32223 | — | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/altair/vegalite/v5/schema/vega-lite-schema.json` | 32223 | — | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/torch/testing/_internal/common_methods_invocations.py` | 27256 | collections, copy, enum, functools, itertools | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/altair/vegalite/v5/schema/core.py` | 27200 | __future__, _typing, altair, collections, json | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/altair/vegalite/v5/schema/core.py` | 27200 | __future__, _typing, altair, collections, json | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/altair/vegalite/v5/schema/core.py` | 27200 | __future__, _typing, altair, collections, json | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/altair/vegalite/v5/schema/core.py` | 27200 | __future__, _typing, altair, collections, json | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/plotly/graph_objs/_figurewidget.py` | 25399 | plotly | |

### smc-analysis

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/m3_signals/signal_adapter.py` | 3660 | __future__, collections, os, shared, sys | |
| `Crypto Analysis/m3_signals/signals.py` | 1332 | __future__, datetime, threading | |
| `Crypto Analysis/m5_backtest/m4_backtest.py` | 1073 | argparse, collections, concurrent, datetime, json | |
| `Crypto Analysis/run_pipeline.py` | 673 | __future__, argparse, data, datetime, json | |
| `Crypto Analysis/m5_backtest/train_m35.py` | 649 | argparse, data, datetime, json, m3_5_dnn | |
| `Crypto Analysis/shared/signal_schema.py` | 619 | __future__, dataclasses, math, typing | |
| `Crypto Analysis/m4_risk/signal_receiver.py` | 452 | __future__, logging, m4_risk, os, shared | |
| `Crypto Analysis/m5_backtest/_tiered_signal_system.py` | 452 | collections, datetime, itertools, m3_signals, m5_backtest | |
| `Crypto Analysis/m4_risk/fusion/xgb_fusion.py` | 399 | __future__, m4_risk, numpy, os, pickle | |
| `Crypto Analysis/tests/test_e2e.py` | 353 | data, m1_5_daily, m3_5_dnn, m3_signals, m4_risk | |
| `Crypto Analysis/m5_backtest/compare_m3_vs_m35.py` | 314 | argparse, m3_5_dnn, m5_backtest, numpy, os | |
| `Crypto Analysis/m5_backtest/_signal_calibration.py` | 192 | collections, datetime, m5_backtest, numpy, os | |
| `Crypto Analysis/reports/report_20260601T205859_ETHUSDT.html` | 124 | — | |
| `Crypto Analysis/reports/report_20260601T210136_ETHUSDT.html` | 124 | — | |
| `Crypto Analysis/reports/report_20260601T210137_SOLUSDT.html` | 124 | — | |

### war-room-dashboard

| 檔案 | 行數 | 主要依賴 | 決定 |
|---|---|---|---|
| `Crypto Analysis/CLAUDE.md` | 346 | — | |
| `Crypto Analysis/dev_sandbox/venv_py311/Lib/site-packages/tornado/wsgi.py` | 269 | _typeshed, concurrent, io, sys, tornado | |
| `Crypto Analysis/dev_sandbox/venv_py312/Lib/site-packages/tornado/wsgi.py` | 269 | _typeshed, concurrent, io, sys, tornado | |
| `Crypto Analysis/dev_sandbox/venv_py313/Lib/site-packages/tornado/wsgi.py` | 269 | _typeshed, concurrent, io, sys, tornado | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/tornado/wsgi.py` | 269 | _typeshed, concurrent, io, sys, tornado | |
| `Crypto Analysis/dev_sandbox/venv_st/Lib/site-packages/pygments/lexers/_cocoa_builtins.py` | 76 | os, re | |
| `Crypto Analysis/dev_sandbox/reports/py314_incompat_diagnostic.md` | 72 | — | |
