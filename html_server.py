from flask import Flask, request, jsonify, send_from_directory
import subprocess, os, signal, sys, json
from datetime import datetime

app = Flask(__name__)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Run scrape.py
@app.route("/api/run_simple", methods=["POST"])
def run_simple():
    try:
        script_path = os.path.join(ROOT_DIR, "scrape.py")
        if not os.path.exists(script_path):
            return jsonify({"error": "scrape.py not found"}), 404
        # Run in background (non-blocking)
        subprocess.Popen([sys.executable, script_path], cwd=ROOT_DIR)
        return jsonify({"status": "started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete database.json
@app.route("/api/reset", methods=["POST"])
def reset_database():
    db_path = os.path.join(ROOT_DIR, "database.json")
    try:
        print("🔄 Deleting database.json")
        if os.path.exists(db_path):
            os.remove(db_path)
            return jsonify({"status": "deleted"}), 200
        else:
            return jsonify({"status": "no file"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# For JS ping check
@app.route("/api/last_modified", methods=["GET"])
def last_modified():
    db_path = os.path.join(ROOT_DIR, "database.json")
    if not os.path.exists(db_path):
        return jsonify({"last_modified": None})
    ts = os.path.getmtime(db_path)
    return jsonify({"last_modified": datetime.fromtimestamp(ts).isoformat()})


# Serve generated HTML page
@app.route("/")
def index():
    html_dir = os.path.join(ROOT_DIR, "html_pages")
    return send_from_directory(html_dir, "main_page.html")


# API: Graceful shutdown
@app.route("/api/exit", methods=["POST"])
def exit_program():
    # In production just show alert; during local run, actually exit
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"status": "terminated"})


if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # hides info & warning messages
    app.run(port=5000, debug=False)