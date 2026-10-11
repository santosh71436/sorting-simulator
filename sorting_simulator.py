"""
Selection Sort vs Insertion Sort - Performance Simulator
Run:  pip install streamlit pandas altair
      streamlit run sorting_simulator.py
"""
import random
import time
import tracemalloc

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Selection vs Insertion Sort", page_icon="📊", layout="wide")

INPUT_TYPES = ["Random", "Already sorted", "Reverse sorted", "Nearly sorted", "Few unique values"]
ROLE_COLORS = {
    "unsorted": "#9ca3af",
    "sorted": "#22c55e",
    "compare": "#f59e0b",
    "min": "#3b82f6",
    "key": "#a855f7",
    "swap": "#ef4444",
}


# ----------------------------------------------------------------------------
# Input generation
# ----------------------------------------------------------------------------
def make_input(kind: str, n: int, seed: int = 42):
    rng = random.Random(seed)
    if kind == "Random":
        a = list(range(1, n + 1))
        rng.shuffle(a)
    elif kind == "Already sorted":
        a = list(range(1, n + 1))
    elif kind == "Reverse sorted":
        a = list(range(n, 0, -1))
    elif kind == "Nearly sorted":
        a = list(range(1, n + 1))
        for _ in range(max(1, n // 20)):  # ~5% of elements displaced slightly
            i = rng.randrange(n)
            j = min(n - 1, i + rng.randint(1, 3))
            a[i], a[j] = a[j], a[i]
    else:  # Few unique values
        a = [rng.randint(1, 5) * 10 for _ in range(n)]
    return a


# ----------------------------------------------------------------------------
# Fast algorithms (used for benchmarking). Return (comparisons, writes).
# "writes" = element assignments/swap-writes into the array.
# ----------------------------------------------------------------------------
def selection_sort(a):
    n = len(a)
    comps = writes = 0
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            comps += 1
            if a[j] < a[m]:
                m = j
        if m != i:
            a[i], a[m] = a[m], a[i]
            writes += 2
    return comps, writes


def insertion_sort(a):
    comps = writes = 0
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0:
            comps += 1
            if a[j] > key:
                a[j + 1] = a[j]
                writes += 1
                j -= 1
            else:
                break
        a[j + 1] = key
        writes += 1
    return comps, writes


def selection_sort_plain(a):  # no counters -> fair wall-clock timing
    n = len(a)
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            if a[j] < a[m]:
                m = j
        if m != i:
            a[i], a[m] = a[m], a[i]


def insertion_sort_plain(a):
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key


ALGOS = {
    "Selection Sort": (selection_sort, selection_sort_plain),
    "Insertion Sort": (insertion_sort, insertion_sort_plain),
}


# ----------------------------------------------------------------------------
# Step-by-step frame generators (used for the visual simulator)
# ----------------------------------------------------------------------------
def selection_frames(data):
    a = list(data)
    n = len(a)
    comps = writes = 0
    frames = []

    def snap(note, roles, sorted_upto):
        frames.append(dict(arr=a.copy(), roles=dict(roles), sorted_upto=sorted_upto,
                           comps=comps, writes=writes, note=note))

    snap("Initial array", {}, 0)
    for i in range(n - 1):
        m = i
        snap(f"Pass {i + 1}: assume position {i} holds the minimum ({a[m]})", {m: "min"}, i)
        for j in range(i + 1, n):
            comps += 1
            snap(f"Compare a[{j}]={a[j]} with current min a[{m}]={a[m]}", {m: "min", j: "compare"}, i)
            if a[j] < a[m]:
                m = j
                snap(f"New minimum found at position {m} ({a[m]})", {m: "min"}, i)
        if m != i:
            a[i], a[m] = a[m], a[i]
            writes += 2
            snap(f"Swap minimum into position {i}", {i: "swap", m: "swap"}, i + 1)
        else:
            snap(f"Minimum already at position {i}; no swap", {i: "min"}, i + 1)
    snap("Sorted!", {}, n)
    return frames


def insertion_frames(data):
    a = list(data)
    n = len(a)
    comps = writes = 0
    frames = []

    def snap(note, roles, sorted_upto):
        frames.append(dict(arr=a.copy(), roles=dict(roles), sorted_upto=sorted_upto,
                           comps=comps, writes=writes, note=note))

    snap("Initial array (first element is a sorted run of size 1)", {}, 1)
    for i in range(1, n):
        key = a[i]
        j = i - 1
        snap(f"Pick key = {key} from position {i}", {i: "key"}, i)
        while j >= 0:
            comps += 1
            snap(f"Compare a[{j}]={a[j]} with key={key}", {j: "compare", j + 1: "key"}, i)
            if a[j] > key:
                a[j + 1] = a[j]
                writes += 1
                snap(f"{a[j + 1]} > {key}: shift right to position {j + 1}", {j + 1: "swap"}, i)
                j -= 1
            else:
                break
        a[j + 1] = key
        writes += 1
        snap(f"Insert key {key} at position {j + 1}", {j + 1: "key"}, i + 1)
    snap("Sorted!", {}, n)
    return frames


def draw_frame(frame):
    n = len(frame["arr"])
    roles = []
    for i in range(n):
        if i in frame["roles"]:
            roles.append(frame["roles"][i])
        elif i < frame["sorted_upto"]:
            roles.append("sorted")
        else:
            roles.append("unsorted")
    df = pd.DataFrame({"index": list(range(n)), "value": frame["arr"], "role": roles})
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("index:O", axis=None),
            y=alt.Y("value:Q", axis=None),
            color=alt.Color(
                "role:N",
                scale=alt.Scale(domain=list(ROLE_COLORS), range=list(ROLE_COLORS.values())),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["index", "value", "role"],
        )
        .properties(height=340)
    )
    return chart


# ----------------------------------------------------------------------------
# Benchmark helpers
# ----------------------------------------------------------------------------
def time_sort(fn, data, repeats):
    best = float("inf")
    for _ in range(repeats):
        a = list(data)
        t0 = time.perf_counter()
        fn(a)
        best = min(best, time.perf_counter() - t0)
    return best * 1000  # ms


def peak_aux_memory(fn, data):
    a = list(data)  # allocated before tracing, so only auxiliary memory is counted
    tracemalloc.start()
    tracemalloc.reset_peak()
    base = tracemalloc.get_traced_memory()[0]
    fn(a)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return max(0, peak - base)


def is_stable_check(fn_counted):
    """Empirically test stability using (key, tag) pairs via a tiny wrapper class."""
    class Item:
        def __init__(self, k, t):
            self.k, self.t = k, t

        def __lt__(self, o):
            return self.k < o.k

        def __gt__(self, o):
            return self.k > o.k

    items = [Item(k, t) for t, k in enumerate([3, 1, 3, 2, 1, 3, 2, 1])]
    fn_counted(items)
    seen = {}
    for it in items:
        seen.setdefault(it.k, []).append(it.t)
    return all(v == sorted(v) for v in seen.values())


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.title("📊 Selection Sort vs Insertion Sort")
st.caption("Visual simulator, empirical benchmark, and analysis of time, space and input characteristics.")

tab_sim, tab_bench, tab_space, tab_theory = st.tabs(
    ["🎬 Visual Simulator", "⏱️ Time Benchmark", "💾 Space Analysis", "📚 Theory & Verdict"]
)

# ---------------------------- Simulator tab ---------------------------------
with tab_sim:
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1, 1])
    algo_name = c1.selectbox("Algorithm", list(ALGOS), key="sim_algo")
    kind = c2.selectbox("Input type", INPUT_TYPES, key="sim_kind")
    n = c3.slider("Array size", 5, 40, 20, key="sim_n")
    seed = c4.number_input("Seed", 0, 9999, 42, key="sim_seed")

    custom = st.text_input("…or enter your own numbers (comma separated, overrides the above)", "")
    if custom.strip():
        try:
            data = [int(x) for x in custom.split(",") if x.strip()]
            if not 2 <= len(data) <= 60:
                raise ValueError
        except ValueError:
            st.error("Enter 2-60 integers separated by commas.")
            st.stop()
    else:
        data = make_input(kind, n, int(seed))

    gen = selection_frames if algo_name == "Selection Sort" else insertion_frames
    sig = (algo_name, tuple(data))
    if st.session_state.get("sim_sig") != sig:
        st.session_state.sim_sig = sig
        st.session_state.frames = gen(data)
        st.session_state.frame_idx = 0
    frames = st.session_state.frames

    p1, p2, p3 = st.columns([1, 1, 2])
    speed = p3.slider("Playback delay (ms)", 10, 800, 120, step=10)
    play = p1.button("▶️ Play", width="stretch")
    if p2.button("⏮️ Reset", width="stretch"):
        st.session_state.frame_idx = 0

    idx = st.slider("Step", 0, len(frames) - 1, key="frame_idx")

    view = st.empty()
    info = st.empty()

    def render(i):
        f = frames[i]
        with view.container():
            st.altair_chart(draw_frame(f), width="stretch")
        with info.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("Comparisons so far", f["comps"])
            m2.metric("Array writes so far", f["writes"])
            m3.metric("Step", f"{i} / {len(frames) - 1}")
            st.info(f["note"])

    if play:
        start = idx if idx < len(frames) - 1 else 0
        for i in range(start, len(frames)):
            render(i)
            time.sleep(speed / 1000)
    else:
        render(idx)

    st.caption(
        "Legend - blue: current minimum · amber: element being compared · purple: key (insertion) · "
        "red: swap/shift · green: sorted region"
    )

# ---------------------------- Benchmark tab ---------------------------------
with tab_bench:
    st.subheader("Empirical comparison across input sizes and input characteristics")
    b1, b2 = st.columns(2)
    sizes = b1.multiselect("Input sizes (n)", [50, 100, 250, 500, 1000, 2000, 3000],
                           default=[100, 250, 500, 1000, 2000])
    kinds = b2.multiselect("Input types", INPUT_TYPES, default=INPUT_TYPES)
    repeats = st.slider("Timing repeats (best-of)", 1, 5, 2)
    st.caption("Pure-Python implementations: n = 3000 can take several seconds per run on reverse-sorted input.")

    if st.button("🚀 Run benchmark", type="primary"):
        if not sizes or not kinds:
            st.warning("Pick at least one size and one input type.")
        else:
            rows = []
            total = len(sizes) * len(kinds) * 2
            bar = st.progress(0.0)
            done = 0
            for kd in kinds:
                for sz in sorted(sizes):
                    data = make_input(kd, sz)
                    for name, (counted, plain) in ALGOS.items():
                        a = list(data)
                        comps, writes = counted(a)
                        assert a == sorted(data), "sort failed"
                        ms = time_sort(plain, data, repeats)
                        rows.append(dict(Algorithm=name, Input=kd, n=sz, Comparisons=comps,
                                         Writes=writes, **{"Time (ms)": round(ms, 3)}))
                        done += 1
                        bar.progress(done / total)
            bar.empty()
            st.session_state.bench = pd.DataFrame(rows)

    if "bench" in st.session_state:
        df = st.session_state.bench
        log = st.checkbox("Log-log axes (slope reveals growth order)", value=False)
        scale = alt.Scale(type="log") if log else alt.Scale(type="linear")
        metric = st.radio("Metric", ["Time (ms)", "Comparisons", "Writes"], horizontal=True)

        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("n:Q", scale=scale, title="Input size n"),
                y=alt.Y(f"{metric}:Q", scale=scale),
                color="Algorithm:N",
                tooltip=["Algorithm", "Input", "n", "Comparisons", "Writes", "Time (ms)"],
            )
            .properties(width=220, height=240)
            .facet(column=alt.Column("Input:N", sort=INPUT_TYPES))
        )
        st.altair_chart(chart)

        st.markdown("#### Raw results")
        st.dataframe(df, width="stretch", hide_index=True)

        st.markdown("#### Who wins at the largest n for each input type?")
        nmax = df["n"].max()
        verdicts = []
        for kd in df["Input"].unique():
            sub = df[(df["Input"] == kd) & (df["n"] == nmax)].set_index("Algorithm")
            if len(sub) < 2:
                continue
            s, i = sub.loc["Selection Sort"], sub.loc["Insertion Sort"]
            ratio = s["Time (ms)"] / max(i["Time (ms)"], 1e-9)
            winner = "Insertion Sort" if ratio > 1 else "Selection Sort"
            verdicts.append({
                "Input": kd, "n": nmax,
                "Selection time (ms)": s["Time (ms)"], "Insertion time (ms)": i["Time (ms)"],
                "Faster": winner, "Speed ratio": f"{max(ratio, 1 / ratio):.2f}×",
                "Selection writes": s["Writes"], "Insertion writes": i["Writes"],
            })
        st.dataframe(pd.DataFrame(verdicts), width="stretch", hide_index=True)
    else:
        st.info("Configure the options above and click **Run benchmark**.")

# ---------------------------- Space tab -------------------------------------
with tab_space:
    st.subheader("Auxiliary space measured with `tracemalloc`")
    sp_sizes = st.multiselect("Sizes", [100, 500, 1000, 2000], default=[100, 500, 1000, 2000], key="sp")
    if st.button("Measure memory"):
        rows = []
        for sz in sorted(sp_sizes):
            data = make_input("Random", sz)
            for name, (_, plain) in ALGOS.items():
                rows.append(dict(Algorithm=name, n=sz, **{"Peak extra memory (bytes)": peak_aux_memory(plain, data)}))
        mdf = pd.DataFrame(rows)
        st.altair_chart(
            alt.Chart(mdf).mark_line(point=True).encode(
                x="n:Q", y=alt.Y("Peak extra memory (bytes):Q", scale=alt.Scale(domain=[0, max(1024, mdf.iloc[:, 2].max() * 1.5)])),
                color="Algorithm:N").properties(height=300),
            width="stretch")
        st.dataframe(mdf, width="stretch", hide_index=True)
        st.success("Extra memory stays a small constant while n grows → both sorts are O(1) auxiliary space (in-place).")

    st.markdown(
        "Both algorithms only use a handful of scalar variables (`i`, `j`, `min_idx` / `key`) and sort inside the "
        "input array, so auxiliary space is **O(1)**. Compare with Merge Sort's O(n) buffer."
    )

# ---------------------------- Theory tab ------------------------------------
with tab_theory:
    st.subheader("Complexity summary")
    theory = pd.DataFrame({
        "Property": ["Best-case time", "Average-case time", "Worst-case time", "Auxiliary space",
                     "Comparisons (worst)", "Writes / swaps (worst)", "Stable?", "Adaptive?", "Online?"],
        "Selection Sort": ["O(n²)", "O(n²)", "O(n²)", "O(1)",
                           "n(n-1)/2", "≤ n-1 swaps → O(n)", "No (long-distance swaps)", "No", "No"],
        "Insertion Sort": ["O(n)  (already sorted)", "O(n²)", "O(n²)  (reverse sorted)", "O(1)",
                           "n(n-1)/2", "≈ n²/2 shifts → O(n²)", "Yes", "Yes - O(n + inversions)", "Yes"],
    })
    st.dataframe(theory, width="stretch", hide_index=True)

    sa = is_stable_check(lambda x: selection_sort(x))
    ia = is_stable_check(lambda x: insertion_sort(x))
    st.markdown(f"**Live stability test** (equal keys tagged with original order): "
                f"Selection Sort stable = `{sa}`, Insertion Sort stable = `{ia}`")

    st.subheader("Effect of input characteristics")
    st.dataframe(pd.DataFrame({
        "Input": INPUT_TYPES,
        "Selection Sort": [
            "≈ n²/2 comparisons, ≤ n swaps",
            "Still n²/2 comparisons (no early exit), 0 swaps",
            "n²/2 comparisons, ~n/2 swaps",
            "n²/2 comparisons - unaffected by order",
            "n²/2 comparisons - duplicates give no benefit"],
        "Insertion Sort": [
            "≈ n²/4 comparisons and shifts",
            "n-1 comparisons, 0 shifts → O(n) best case",
            "n²/2 comparisons and shifts → worst case",
            "≈ n + (few inversions) → close to O(n)",
            "Fewer shifts than random (equal keys don't move)"],
    }), width="stretch", hide_index=True)

    st.subheader("When to choose which")
    st.markdown(
        "- **Insertion Sort**: small or nearly-sorted data, streaming/online input, need stability, or used as the "
        "base case of hybrid sorts (Timsort, introsort switch to it for tiny partitions).\n"
        "- **Selection Sort**: when *writes are expensive* (e.g. flash/EEPROM) because it performs at most n-1 swaps; "
        "its running time is predictable regardless of input.\n"
        "- **Neither** for large random data → use O(n log n) algorithms (merge, quick, heap sort)."
    )
