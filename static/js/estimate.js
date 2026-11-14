// グローバル変数
let selectedFiles = {
    managementFile: '',
    priceList: '',
    outputFolder: ''
};

let currentSessionId = '';
let currentManagementFilePath = '';
let currentPriceListPath = '';
let generatedEstimateFiles = [];

// ステップ①：見積入力行を動的に管理
function addEstimateRow(index = null) {
    const container = document.getElementById('estimate-rows-container');
    const rowCount = container.querySelectorAll('.input-row').length;
    const newIndex = index !== null ? index : rowCount;

    const rowHtml = `
        <div class="input-row" data-row-index="${newIndex}">
            <input type="text" placeholder="例：双日" class="company-input" value="">
            <input type="text" placeholder="例：クレジットカード審査システム" class="project-input" value="">
            <input type="text" placeholder="例：山田太郎" class="person-input" value="">
            <input type="text" placeholder="例：2026/11/1 ～ 2027/3/31" class="deadline-input" value="">
            <input type="text" placeholder="例：5.00" class="period-input" value="">
            <input type="text" placeholder="例：5.00" class="workload-input" value="">
            <button class="btn btn-danger" onclick="removeEstimateRow(this)">削除</button>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', rowHtml);
    console.log(`見積入力行を追加しました（行番号: ${newIndex + 1}）`);
}

function removeEstimateRow(button) {
    button.closest('.input-row').remove();
    console.log('見積入力行を削除しました');
}

function getEstimateRows() {
    const rows = [];
    document.querySelectorAll('.input-row').forEach(rowEl => {
        const company = rowEl.querySelector('.company-input').value.trim();
        const project = rowEl.querySelector('.project-input').value.trim();
        const person = rowEl.querySelector('.person-input').value.trim();
        const deadline = rowEl.querySelector('.deadline-input').value.trim();
        const periodStr = rowEl.querySelector('.period-input').value.trim();
        const workloadStr = rowEl.querySelector('.workload-input').value.trim();

        const row = {
            company: company,
            project: project,
            person: person,
            deadline: deadline,
            period: periodStr ? parseFloat(periodStr) : '',
            workload: workloadStr ? parseFloat(workloadStr) : ''
        };
        rows.push(row);
    });
    return rows;
}

// ステップ②：ファイル選択
function handleFileSelect(input, fileType) {
    if (input.files.length > 0) {
        const fileName = input.files[0].name;
        selectedFiles[fileType] = fileName;

        let displayElementId = '';
        if (fileType === 'managementFile') {
            displayElementId = 'management-file-path';
        } else if (fileType === 'priceList') {
            displayElementId = 'price-list-path';
        }

        if (displayElementId) {
            document.getElementById(displayElementId).textContent = fileName;
        }
        console.log(`${fileType} を選択しました: ${fileName}`);
    }
}

function handleFolderSelect(input) {
    if (input.files.length > 0) {
        const folderName = input.files[0].webkitRelativePath.split('/')[0];
        selectedFiles.outputFolder = folderName;
        document.getElementById('output-folder-path').textContent = folderName;
        console.log(`フォルダを選択しました: ${folderName}`);
    }
}

// API呼び出し
async function writeContent() {
    const rows = getEstimateRows();
    const messageEl = document.getElementById('message-step2');

    if (rows.length === 0) {
        showMessage(messageEl, 'error', 'エラー：見積データが入力されていません');
        return;
    }

    const managementPath = document.getElementById('management-file-path-input').value.trim();
    const priceListPath = document.getElementById('price-list-path-input').value.trim();

    if (!managementPath || !priceListPath) {
        showMessage(messageEl, 'error', 'エラー：管理ファイルと金額リストの両方を指定してください');
        return;
    }

    showMessage(messageEl, 'info', '⏳ 処理中...');

    try {
        const response = await fetch('/api/write-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rows: rows,
                managementFile: managementPath,
                priceList: priceListPath
            })
        });

        const data = await response.json();

        if (data.success) {
            currentSessionId = data.session_id;
            currentManagementFilePath = managementPath;
            currentPriceListPath = priceListPath;
            showMessage(messageEl, 'success', `✅ ${data.message}`);

            displayStep2ResultTable(data.data);
            console.log('見積内容が保存されました:', data);
        } else {
            showMessage(messageEl, 'error', `❌ ${data.message}`);
        }
    } catch (error) {
        showMessage(messageEl, 'error', `❌ エラー: ${error.message}`);
        console.error('API呼び出しエラー:', error);
    }
}

async function generateEstimate() {
    const messageEl = document.getElementById('message-step4');
    const outputFolder = document.getElementById('output-folder-path-input').value.trim();

    if (!currentSessionId) {
        showMessage(messageEl, 'error', '❌ エラー：ステップ②を先に実行してください');
        return;
    }

    if (!outputFolder) {
        showMessage(messageEl, 'error', '❌ エラー：ステップ③でフォルダパスを指定してください');
        return;
    }

    showMessage(messageEl, 'info', '⏳ 見積書を生成中...');

    try {
        const response = await fetch('/api/generate-estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                output_folder: outputFolder,
                management_file: currentManagementFilePath,
                price_list: currentPriceListPath
            })
        });

        const data = await response.json();

        if (data.success) {
            showMessage(messageEl, 'success', `✅ ${data.message}\n\n保存先：${outputFolder}`);
            displayResultTable(data.files);
            generatedEstimateFiles = data.files;
            console.log('見積書が生成されました:', data);
        } else {
            showMessage(messageEl, 'error', `❌ ${data.message}`);
        }
    } catch (error) {
        showMessage(messageEl, 'error', `❌ エラー: ${error.message}`);
        console.error('API呼び出しエラー:', error);
    }
}

async function generatePDF() {
    const messageEl = document.getElementById('message-step5');
    const outputFolder = document.getElementById('output-folder-path-input').value.trim();

    if (!outputFolder) {
        showMessage(messageEl, 'error', '❌ エラー：ステップ③でフォルダパスを指定してください');
        return;
    }

    if (generatedEstimateFiles.length === 0) {
        showMessage(messageEl, 'error', '❌ エラー：ステップ④で見積書を生成してください');
        return;
    }

    showMessage(messageEl, 'info', '⏳ PDF見積書を生成中...');

    try {
        const response = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                output_folder: outputFolder,
                excel_files: generatedEstimateFiles
            })
        });

        const data = await response.json();

        if (data.success) {
            showMessage(messageEl, 'success', `✅ ${data.message}\n\n保存先：${outputFolder}`);
            displayPDFResultTable(data.files);
            console.log('PDF見積書が生成されました:', data);
        } else {
            showMessage(messageEl, 'error', `❌ ${data.message}`);
        }
    } catch (error) {
        showMessage(messageEl, 'error', `❌ エラー: ${error.message}`);
        console.error('API呼び出しエラー:', error);
    }
}

// UI ユーティリティ
function showMessage(element, type, message) {
    element.className = `message ${type}`;
    element.textContent = message;
}

function displayStep2ResultTable(rows) {
    const container = document.getElementById('step2-result-container');
    const tbody = document.getElementById('step2-result-body');
    tbody.innerHTML = '';

    rows.forEach((row, index) => {
        const tr = document.createElement('tr');
        let unitPriceDisplay = '-';
        let amountDisplay = '-';

        if (row.unit_price !== undefined && row.unit_price !== null) {
            unitPriceDisplay = row.unit_price > 0 ? `¥${row.unit_price.toLocaleString()}` : '-';
        }

        if (row.amount !== undefined && row.amount !== null) {
            amountDisplay = row.amount > 0 ? `¥${row.amount.toLocaleString()}` : '-';
        } else if (row.period && row.period > 0) {
            amountDisplay = 'エラー（単価が見つかりません）';
        }

        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${row.company || '-'}</td>
            <td>${row.project || '-'}</td>
            <td>${row.person || '-'}</td>
            <td>${row.deadline || '-'}</td>
            <td>${row.period || '-'}</td>
            <td>${unitPriceDisplay}</td>
            <td>${amountDisplay}</td>
        `;
        tbody.appendChild(tr);
    });

    container.style.display = 'block';
}

function displayResultTable(files) {
    const container = document.getElementById('result-container');
    const tbody = document.getElementById('result-body');
    tbody.innerHTML = '';

    files.forEach((file, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${file}</td>
        `;
        tbody.appendChild(tr);
    });

    container.style.display = 'block';
}

function displayPDFResultTable(files) {
    const container = document.getElementById('pdf-result-container');
    const tbody = document.getElementById('pdf-result-body');
    tbody.innerHTML = '';

    files.forEach((file, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${file}</td>
        `;
        tbody.appendChild(tr);
    });

    container.style.display = 'block';
}

// 初期化
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();

        if (data.success) {
            const config = data.data;
            document.getElementById('management-file-path-input').value = config.managementFile || '';
            document.getElementById('price-list-path-input').value = config.priceListFile || '';
            document.getElementById('output-folder-path-input').value = config.outputFolder || '';
            console.log('設定を読み込みました');
        }
    } catch (error) {
        console.log('設定ファイルがない場合はスキップ');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('ページが読み込まれました');
    addEstimateRow();
    loadConfig();
});
