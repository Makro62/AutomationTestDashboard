import os
import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Path ke output.xml dan history.json
OUTPUT_XML_PATH = os.path.join("..", "results", "output.xml")
HISTORY_JSON_PATH = os.path.join("..", "results", "history.json")

# Global variables untuk test execution
test_processes = {}
test_status = {}
test_results = {}

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


def run_test_suite(suite_type, test_name=None, headless=True):
    """
    Jalankan test suite dengan parameter yang diberikan
    
    Args:
        suite_type: 'web', 'mobile', atau 'api'
        test_name: Nama test spesifik (optional)
        headless: Apakah menjalankan browser dalam mode headless
        
    Returns:
        dict: Status eksekusi test
    """
    try:
        # Buat output directory
        output_dir = f"../results/{suite_type}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Command untuk menjalankan test
        cmd = [
            "robot",
            "--outputdir", output_dir,
            "--output", f"{suite_type}_results.xml",
            "--log", f"{suite_type}_log.html",
            "--report", f"{suite_type}_report.html"
        ]
        
        # Tambahkan headless mode untuk web tests
        if suite_type == "web" and headless:
            cmd.extend(["--variable", "BROWSER_HEADLESS:True"])
        elif suite_type == "web" and not headless:
            cmd.extend(["--variable", "BROWSER_HEADLESS:False"])
        
        # Tambahkan test spesifik jika ada
        if test_name:
            cmd.extend(["--test", test_name])
        
        # Tambahkan path test suite - disesuaikan dengan struktur folder baru
        if suite_type == "web":
            cmd.append("../tests/")
        else:
            cmd.append(f"../tests/{suite_type}/")
        
        print(f"[INFO] Menjalankan command: {' '.join(cmd)}")
        
        # Jalankan test dalam thread terpisah
        def run_test():
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                test_processes[suite_type] = process
                test_status[suite_type] = "running"
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    test_status[suite_type] = "completed"
                    test_results[suite_type] = {
                        "status": "PASS",
                        "output": stdout,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    test_status[suite_type] = "failed"
                    test_results[suite_type] = {
                        "status": "FAIL",
                        "error": stderr,
                        "output": stdout,
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                test_status[suite_type] = "error"
                test_results[suite_type] = {
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Start thread
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        return {
            "status": "started",
            "suite": suite_type,
            "test_name": test_name,
            "headless": headless,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[ERROR] Gagal menjalankan test suite {suite_type}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_test_status(suite_type):
    """Get status test yang sedang berjalan"""
    return {
        "suite": suite_type,
        "status": test_status.get(suite_type, "idle"),
        "result": test_results.get(suite_type, {}),
        "timestamp": datetime.now().isoformat()
    }


def stop_test_suite(suite_type):
    """Stop test suite yang sedang berjalan"""
    try:
        if suite_type in test_processes:
            process = test_processes[suite_type]
            if process.poll() is None:  # Process masih berjalan
                process.terminate()
                test_status[suite_type] = "stopped"
                return {"status": "stopped", "suite": suite_type}
            else:
                return {"status": "not_running", "suite": suite_type}
        else:
            return {"status": "not_found", "suite": suite_type}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.route("/")
def home():
    result = parse_results()
    print("[DEBUG] Data hasil parsing:", result)
    save_history(result)
    return render_template("index.html", result=result, history=load_history())


@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


@app.route("/api/run-test", methods=["POST"])
def api_run_test():
    """API endpoint untuk menjalankan test"""
    try:
        data = request.get_json()
        suite_type = data.get("suite_type", "web")
        test_name = data.get("test_name")
        headless = data.get("headless", True)
        
        if suite_type not in ["web", "mobile", "api"]:
            return jsonify({"error": "Invalid suite type"}), 400
        
        result = run_test_suite(suite_type, test_name, headless)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/test-status/<suite_type>")
def api_test_status(suite_type):
    """API endpoint untuk mendapatkan status test"""
    try:
        if suite_type not in ["web", "mobile", "api"]:
            return jsonify({"error": "Invalid suite type"}), 400
        
        status = get_test_status(suite_type)
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop-test/<suite_type>", methods=["POST"])
def api_stop_test(suite_type):
    """API endpoint untuk menghentikan test"""
    try:
        if suite_type not in ["web", "mobile", "api"]:
            return jsonify({"error": "Invalid suite type"}), 400
        
        result = stop_test_suite(suite_type)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/test-results")
def api_test_results():
    """API endpoint untuk mendapatkan hasil test"""
    try:
        result = parse_results()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/available-tests")
def api_available_tests():
    """API endpoint untuk mendapatkan daftar test yang tersedia"""
    try:
        tests = {
            "web": [],
            "mobile": [],
            "api": []
        }
        
        # Scan test files
        for suite_type in ["web", "mobile", "api"]:
            if suite_type == "web":
                test_dir = "../tests/"
            else:
                test_dir = f"../tests/{suite_type}/"
            
            if os.path.exists(test_dir):
                for file in os.listdir(test_dir):
                    if file.endswith(".robot"):
                        tests[suite_type].append({
                            "file": file,
                            "name": file.replace(".robot", ""),
                            "path": os.path.join(test_dir, file)
                        })
        
        return jsonify(tests)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Try different ports if 5000 is busy
    import socket
    
    def find_free_port(start_port=5000):
        port = start_port
        while port < start_port + 10:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                port += 1
        return 5001  # fallback
    
    port = find_free_port()
    print(f"🚀 Starting dashboard on port {port}")
    print(f"🌐 Dashboard available at: http://localhost:{port}")
    
    app.run(debug=True, host="0.0.0.0", port=port)

