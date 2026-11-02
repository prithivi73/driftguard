# Drift-Guard
Self-correcting floating-point drift monitor for long-running real-time systems.
Demo: Patriot missile clock failure (Dhahran, 1991).

**Author:** Prithiviraj M (Jack) | USN 25BTRCB037 | Computer Architecture | Jain (Deemed-to-be) University, Bengaluru

## What it does
- Runs an exact integer shadow clock beside the floating-point clock
- Detects drift at runtime, predicts when it crosses a danger limit, re-syncs without a reboot
- Dashboard: drift graph (with vs without), tracking error in metres, IEEE 754 view of 0.1

## Run
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push to GitHub, then share.streamlit.io > New app > pick repo > main file `app.py`.
