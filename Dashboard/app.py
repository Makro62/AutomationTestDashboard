import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Path ke output.xml dan history.json
OUTPUT_XML_PATH = os.path.join("..", "output.xml")
HISTORY_JSON_PATH = os.path.join("..", "history.json")

def parse_results():
    """Parse output.xml dan kembalikan data hasil test"""
    if not os.path.exists(OUTPUT_XML_PATH):
        return {"summary": {"total": 0, "passed": 0, "failed": 0}, "web": [], "mobile": [], "api": []}

    try:
        tree = ET.parse(OUTPUT_XML_PATH)
        root = tree.getroot()
        results = {"web": [], "mobile": [], "api": []}

        for test in root.findall(".//test"):
            name = test.get("name", "Unnamed Test")

            # Ambil status dan waktu dari tag <status> di dalam test
            status_elem = test.find("status")
            status = status_elem.get("status") if status_elem is not None else "UNKNOWN"
            start_time = status_elem.get("start") if status_elem is not None else None
            elapsed_ms = float(status_elem.get("elapsed", "0")) if status_elem is not None else 0

            elapsed_total = "N/A"
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = start_dt + timedelta(milliseconds=elapsed_ms)
                    elapsed_total = f"{round(elapsed_ms / 1000, 2)}s"
                except Exception as e:
                    print(f"[ERROR] Gagal parsing waktu: {e}")

            steps = []
            for kw in test.findall(".//kw"):
                keyword = kw.get("name", "Unknown Keyword")
                args = [arg.text.strip() for arg in kw.findall(".//arg") if arg.text]

                kw_status_elem = kw.find("status")
                step_status = kw_status_elem.get("status") if kw_status_elem is not None else "UNKNOWN"
                step_elapsed = "N/A"
                if kw_status_elem is not None:
                    elapsed_kw = float(kw_status_elem.get("elapsed", "0"))
                    step_elapsed = f"{round(elapsed_kw / 1000, 2)}s"

                steps.append({
                    "name": keyword,
                    "args": args,
                    "status": step_status,
                    "elapsed": step_elapsed
                })

            # Menentukan kategori berdasarkan nama suite induk
            parent_suite = test.find("../../..")
            category = "web"  # default
            if parent_suite is not None:
                suite_name = parent_suite.get("name", "").lower()
                if "api" in suite_name:
                    category = "api"
                elif "mobile" in suite_name:
                    category = "mobile"

            results[category].append({
                "name": name,
                "status": status,
                "steps": steps,
                "elapsed_total": elapsed_total
            })

        total = sum(len(tests) for tests in results.values())
        passed = sum(1 for tests in results.values() for test in tests if test["status"] == "PASS")
        failed = total - passed

        results["summary"] = {"total": total, "passed": passed, "failed": failed}
        return results

    except ET.ParseError as e:
        print(f"[ERROR] File output.xml tidak valid: {e}")
    except Exception as e:
        print(f"[ERROR] Gagal parsing hasil test: {e}")

    return {"summary": {"total": 0, "passed": 0, "failed": 0}, "web": [], "mobile": [], "api": []}


def save_history(result):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_summary = result.get("summary", {})

    history = []
    if os.path.exists(HISTORY_JSON_PATH):
        try:
            with open(HISTORY_JSON_PATH, "r") as f:
                history = json.load(f)
            if history:
                last = history[-1].get("summary", {})
                if (last.get("total") == current_summary.get("total") and
                    last.get("passed") == current_summary.get("passed") and
                    last.get("failed") == current_summary.get("failed")):
                    print("[INFO] Tidak ada perubahan hasil. Histori tidak disimpan.")
                    return
        except json.JSONDecodeError:
            print("[WARN] File history.json korup. Akan ditimpa.")

    result["timestamp"] = now
    history.append(result)

    with open(HISTORY_JSON_PATH, "w") as f:
        json.dump(history, f, indent=2)


def load_history():
    if os.path.exists(HISTORY_JSON_PATH):
        try:
            with open(HISTORY_JSON_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("[WARN] history.json tidak dapat dibaca.")
    return []


@app.route("/")
def home():
    result = parse_results()
    print("[DEBUG] Data hasil parsing:", result)
    save_history(result)
    return render_template("index.html", result=result, history=load_history())


if __name__ == "__main__":
    app.run(debug=True)

