"""
Drift-Guard: self-correcting numeric error monitor for long-running real-time systems.
Demo scenario: Patriot missile clock (Dhahran, 1991).
Run:  streamlit run app.py
"""
import math
import numpy as np
import pandas as pd
import streamlit as st

TICK = 0.1            # true tick length (seconds)
SCUD_SPEED = 1676.0   # m/s


# ---------------- CORE ENGINE ----------------
def chopped_tick(frac_bits: int) -> float:
    """0.1 chopped (not rounded) to `frac_bits` fractional bits. Patriot used 23."""
    scale = 2 ** frac_bits
    return math.floor(TICK * scale) / scale


def to_ieee754_32(x: float) -> dict:
    """Return sign / exponent / mantissa bits of x as IEEE 754 single precision."""
    import struct
    bits = format(struct.unpack(">I", struct.pack(">f", x))[0], "032b")
    return {"sign": bits[0], "exponent": bits[1:9], "mantissa": bits[9:]}


def simulate(hours: float, frac_bits: int, limit: float, check_every_s: int, guard: bool):
    """
    Returns a DataFrame of drift vs time.
    Float clock adds the chopped tick each 0.1 s. Shadow clock is an exact integer tick count.
    Drift = float_clock - integer_clock * 0.1.
    With guard on: every `check_every_s`, if predicted drift at next check >= limit, re-sync.
    """
    err_per_tick = TICK - chopped_tick(frac_bits)          # error added each tick
    ticks_per_check = check_every_s * 10
    n_checks = int(hours * 3600 / check_every_s)

    t, drift, corrections = [], [], []
    d = 0.0
    n_corr = 0
    for i in range(1, n_checks + 1):
        d += ticks_per_check * err_per_tick                # drift accumulated this interval
        # Predictor: linear growth -> drift at next check
        predicted_next = d + ticks_per_check * err_per_tick
        if guard and predicted_next >= limit:
            d = 0.0                                        # re-sync from integer shadow counter
            n_corr += 1
        t.append(i * check_every_s / 3600)
        drift.append(d)
        corrections.append(n_corr)
    return pd.DataFrame({"hours": t, "drift_s": drift, "corrections": corrections}), err_per_tick


def time_to_limit_hours(err_per_tick: float, limit: float) -> float:
    return limit / (err_per_tick * 10 * 3600) if err_per_tick > 0 else float("inf")


# ---------------- DASHBOARD ----------------
st.set_page_config(page_title="Drift-Guard", page_icon="🛡️", layout="wide")
st.title("🛡️ Drift-Guard")
st.caption("Self-correcting floating-point drift monitor | Patriot missile scenario | Unit II + Unit IV")

with st.sidebar:
    st.header("Controls")
    hours = st.slider("Hours running", 1, 200, 100)
    bits = st.selectbox("Register precision (fractional bits)", [23, 31, 52], index=0,
                        help="23 = Patriot 24-bit register, 52 = IEEE 754 double mantissa")
    limit = st.select_slider("Danger limit (seconds)", [0.01, 0.05, 0.1, 0.2], value=0.1)
    check = st.select_slider("Check every (seconds)", [10, 30, 60, 300], value=60)

off, err_tick = simulate(hours, bits, limit, check, guard=False)
on, _ = simulate(hours, bits, limit, check, guard=True)

final_err = off["drift_s"].iloc[-1]
miss = final_err * SCUD_SPEED
eta = time_to_limit_hours(err_tick, limit)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Error per tick", f"{err_tick:.3e} s")
c2.metric("Drift WITHOUT Drift-Guard", f"{final_err:.4f} s")
c3.metric("Tracking error (Scud)", f"{miss:,.0f} m")
c4.metric("Predicted time to danger", "never" if eta == float("inf") else f"{eta:,.1f} h")

if final_err >= limit:
    st.error(f"WITHOUT Drift-Guard: drift passed the {limit}s limit. Radar looks about {miss:,.0f} m away. Missile missed.")
else:
    st.success("WITHOUT Drift-Guard: still inside the safe limit at this runtime.")
st.info(f"WITH Drift-Guard: max drift {on['drift_s'].max():.4f} s, {int(on['corrections'].iloc[-1])} auto-corrections, zero reboots.")

chart = pd.DataFrame({
    "Without Drift-Guard": off["drift_s"].values,
    "With Drift-Guard": on["drift_s"].values,
}, index=off["hours"].values)
st.subheader("Clock drift over time")
st.line_chart(chart)

st.subheader("How 0.1 is stored (IEEE 754, 32-bit)")
b = to_ieee754_32(0.1)
st.code(f"sign: {b['sign']} | exponent: {b['exponent']} | mantissa: {b['mantissa']}")
st.caption("0.1 is an endless fraction in binary, so it is cut off. That tiny cut-off error is what piles up.")
