try:
    from .scraper import run_scraper
except ImportError:
    from scraper import run_scraper
try:
    from .ui_components import BasicPage
except ImportError:
    from ui_components import BasicPage

SERVER_PORT = 5001

def main_page(config={}):
    page = BasicPage(title="KIND Project", container_width="650px", container_height="700px")
    page.add_element(page.element_header())
    page.add_element(page.element_date())
    page.add_element(page.element_checkbox("headless", "headless", "Chrome 팝업 없이 실행하기", False))
    buttons = [
        {"button_id": "runBtn", "button_text": "실행", "button_type": "submit", "button_class": "btn btn-primary", "onclick": "executeRunFunction()"},
        {"button_id": "discardBtn", "button_text": "버리기", "button_type": "button", "button_class": "btn btn-danger", "onclick": "discardCompanyData()"}
    ]
    page.add_element(page.element_button_group(buttons))
    page.add_element(page.element_button(
        button_id="backBtn",
        button_text="종료",
        button_type="button",
        button_class="btn btn-secondary",
        onclick="alert('프로그램을 종료합니다.');",
        position="absolute",
        bottom="20px",
        right="20px"
    ))
    execution_message = config.get("execution_message", "프로그램을 실행합니다.")
    run_function = run_scraper
    page.add_script('''
        const SERVER_PORT = ''' + str(SERVER_PORT) + ''';
        const urlParams = new URLSearchParams(window.location.search);

        const CONFIG = {
            runFunction: ''' + (f'"{run_function}"' if run_function else 'null') + ''',
            databaseAddress: ''' + f'"database.json"' + ''',
        };

        function executeRunFunction() {
            const fromDate = document.getElementById('fromDate').value;
            const toDate = document.getElementById('toDate').value;
            const headless = document.getElementById('headless').checked;
            
            const params = {from_date: fromDate, to_date: toDate, headless: headless};
            
            if (CONFIG.runFunction) {
                alert(`''' + execution_message + '''\\n\\nRun Function: ${CONFIG.runFunction}\\nParameters: ${JSON.stringify(params, null, 2)}`);
                fetch(`/api/run/${CONFIG.runFunction}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(params)
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        alert(`${CONFIG.runFunction} 실행이 시작되었습니다.\\n\\n진행상황은 서버 콘솔에서 확인할 수 있습니다.`);
                    } else {
                        alert(`실행 실패: ${result.message}`);
                    }
                })
                .catch(error => {
                    alert(`API 호출 오류: ${error.message}`);
                });
            }
            return false;
        }
        
        function validateAndExecute() {
            return executeRunFunction();
        }
        
        async function discardCompanyData() {
            const urlParams = new URLSearchParams(window.location.search);
            if (confirm(`정말로 "${companyName}"의 ${modeText} 데이터를 삭제하시겠습니까?\\n\\n이 작업은 되돌릴 수 없습니다.`)) {
                try {
                    const response = await fetch(`/api/discard-company-data`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        })
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(`데이터가 성공적으로 삭제되었습니다.`);
                    } else {
                        alert(`데이터 삭제 실패: ${result.message}`);
                    }
                } catch (error) {
                    console.error('데이터 삭제 오류:', error);
                    alert('데이터 삭제 중 오류가 발생했습니다: ' + error.message);
                }
            }
        }
        document.getElementById('configForm').addEventListener('submit', function(e) {
            e.preventDefault();
            validateAndExecute();
        });
    ''')
    return page.generate_html()

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    html_dir = "html_pages"
    if not os.path.exists(html_dir): os.makedirs(html_dir)
    with open(f'{html_dir}/main_page.html', 'w', encoding='utf-8') as f: f.write(main_page())
