from flask import Flask, render_template_string, request, jsonify, send_from_directory
import webbrowser
import threading
import time
import sys
import os
import socket
import json
from scraper import run_scraper as run_batch
from scraper import scrape_once, load_database, save_database
from settings import get
from generate_pages import main_page

app = Flask(__name__)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

result_data = None
server_running = False
current_port = None
ui_opened = False

def find_available_port(start_port=5000):
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available ports found")

@app.route('/')
def index(): return main_page()

@app.route('/main_page.html')
def serve_main_page(): return main_page()

@app.route('/logo.jpg')
def logo(): return send_from_directory(os.path.join(ROOT_DIR, 'resources'), 'logo.jpg')

@app.route('/submit', methods=['POST'])
def submit():
    global result_data
    try:
        data = request.get_json()
        if not data.get('company_name'):
            return jsonify({'success': False, 'message': 'Company name is required'})
        result_data = data
        return jsonify({'success': True})
    except Exception as e: return jsonify({'success': False, 'message': str(e)})

@app.route('/api/run/<function_name>', methods=['POST'])
def run_function(function_name):
    global result_data
    try:
        data = request.get_json()
        
        function_to_mode = {
            'run_hist_scraper': 'hist',
            'run_prc_scraper': 'prc'
        }
        
        mode = function_to_mode.get(function_name)
        if not mode:
            return jsonify({'success': False, 'message': f'Unknown function: {function_name}'})
        
        company_name = (data or {}).get('company_name', '').strip() if isinstance(data, dict) else ''
        
        if not company_name:
            # No company provided: run batch (Excel-driven)
            thread = threading.Thread(target=run_batch, daemon=True)
            thread.start()
            return jsonify({'success': True, 'message': 'Batch run started'})
        else:
            # Single company scraping via scrape_once, then append to DB
            from_date = (data or {}).get('from_date', '20240101').replace('-', '').replace('/', '')
            to_date = (data or {}).get('to_date', '20241231').replace('-', '').replace('/', '')
            keyword = (data or {}).get('keyword') or company_name
            cfg = {
                'from_date': from_date,
                'to_date': to_date,
                'company': company_name,
                'keyword': keyword
            }
            def run_single():
                rows = scrape_once(cfg) or []
                db = load_database()
                aggregated = db.get('rows', [])
                aggregated.extend(rows)
                save_database(aggregated)
            thread = threading.Thread(target=run_single, daemon=True)
            thread.start()
            return jsonify({'success': True, 'message': f'Single run for {company_name} started'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/discard-company-data', methods=['POST'])
def discard_company_data():
    try:      
        db_path = os.path.join(ROOT_DIR, 'database.json')
        database = {}
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True, 
            'message': f'Successfully deleted all data from database'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def start_server():
    global server_running, current_port
    server_running = True
    current_port = find_available_port()
    
    print(f"Starting HTML server on port {current_port}")
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='127.0.0.1', port=current_port, debug=False, use_reloader=False)

def get_user_input():
    global result_data, server_running, current_port, ui_opened
    
    if not server_running:
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()

    start_time = time.time()
    while not current_port and time.time() - start_time < 5:
        time.sleep(0.05)
    
    if current_port and not ui_opened:
        webbrowser.open(f'http://127.0.0.1:{current_port}')
        ui_opened = True
        print(f"✅ HTML UI opened at http://127.0.0.1:{current_port}")
    elif not current_port:
        return None
    
    while server_running:
        if result_data is not None:
            result = result_data
            result_data = None
            return result
        time.sleep(0.1)
    
    return None

def main():
    global server_running
    try:
        while True:
            user_input = get_user_input()
            if not user_input:
                break
            try:
                mode = user_input.get('mode', 'hist')
                if mode not in ['hist', 'prc']:
                    mode = 'hist'
                
                user_input['mode'] = mode
                
                print(f"✅ Starting {mode} scraper...")
                run_scraper(user_input)
                print(f"✅ {mode.upper()} scraper completed successfully!")
                
            except Exception as e:
                print(f"❌ Scraper failed: {e}")
                import traceback
                traceback.print_exc()
        
        print("✅ Program terminated.")
        
    except Exception as e: 
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        server_running = False

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
        server_running = False
    except Exception as e:
        print(f"❌ Server error: {e}")
        server_running = False