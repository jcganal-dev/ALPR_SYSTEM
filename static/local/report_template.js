Chart.defaults.color = '#000';
const qm_ctx = $('quick_metrics_chart').getContext('2d');
const quick_metrics_chart = new Chart(qm_ctx, {
    type: 'pie',
    data: { labels: ['Registered', 'No Gate Pass', 'Unidentified'], datasets: [{ label: 'Vehicle Count', data: [0, 0, 0], backgroundColor: ['rgba(43, 163, 45, 1)', 'rgba(235, 14, 31, 1)', '#FFBF26'] }] },
    options: { animation: false, responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' }, datalabels: { formatter: (value, qm_ctx) => { let sum = 0; let dataArr = qm_ctx.chart.data.datasets[0].data; dataArr.map(data => { sum += data; }); if (value === 0) return null; return (value * 100 / sum).toFixed(2) + "%"; }, color: '#000', }, tooltip: { enabled: false } } },
    plugins: [ChartDataLabels]
});

const vcc_ctx = $('vehicle_classification_chart').getContext('2d');
const vehicle_classification_chart = new Chart(vcc_ctx, {
    type: 'bar',
    data: { labels: ['Tricycle', 'Car', 'Motorcycle'], datasets: [{ label: '', data: [0, 0, 0], backgroundColor: ['#F47982', '#1A74A3', '#FCD657'] }] },
    options: { animation: false, responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, datalabels: { formatter: (value) => { if (value === 0) return null; return value; }, color: '#000', }, tooltip: { enabled: false } }, scales: { x: { grid: { display: false } }, y: { grid: { display: false } } } },
    plugins: [ChartDataLabels]
});

const tv_ctx = $('traffic_volume_chart').getContext('2d');
let curve = 0;
const traffic_volume_chart = new Chart(tv_ctx, {
    type: 'line',
    data: { labels: [0], datasets: [ { label: 'Entry Traffic', data: [0], fill: true, backgroundColor: 'rgba(12,75,5,0.3)', borderColor: '#0C4B05', borderWidth: 2, pointRadius: 1.25, lineTension: curve }, { label: 'Exit Traffic', data: [0], fill: true, backgroundColor: 'rgba(12,5,75,0.3)', borderColor: '#0C054B', borderWidth: 2, pointRadius: 1.25, lineTension: curve } ] },
    options: { animation: false, responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true }, datalabels: { display: false }, tooltip: { enabled: true } }, scales: { x: { grid: { display: false, min: -1 } }, y: { display: true, min: 0, grace: '10%' } } },
    plugins: [ChartDataLabels]
});

let filters = ['All', 'All', 'All', 'All', 'All', 'All', 'date_time', 'DESC'];

function row_builder(row) {
    let gate_name = ['Entrance','Exit'];
    let full_name = row['full_name'] || '';
    let plate_number = row['plate_number'] !== '' ? `<plate>${row['plate_number']}</plate>` : '';
    
    return `<div class="div-cell col-plate">${plate_number}</div>
            <div class="div-cell col-owner"><img src='${row['saved_picture']}' class='saved_picture' onerror='this.src="/static/images/image_not_found.png"'></div>
            <div class="div-cell col-type">${row['vehicle_type']}</div>
            <div class="div-cell col-loc">${gate_name[row['gate_number']-1]}</div>
            <div class="div-cell col-time">${row['date_time']}</div>`;
}

function waitForImagesToLoad() {
    const images = document.querySelectorAll('#table_content img');
    const promises = Array.from(images).map(img => {
        if (img.complete) return Promise.resolve();
        return new Promise(resolve => { img.onload = resolve; img.onerror = resolve; });
    });
    return Promise.all(promises);
}

function generatePDFBlob() {
    return new Promise((resolve, reject) => {
        window.scrollTo(0, 0);
        const element = $('your-main-wrapper'); 

        const options = {
            margin: [15,15,15,15], 
            image: { type: 'jpeg', quality: 1 },
            html2canvas: { scale: 2, logging: false, useCORS: true, scrollY: 0 },
            jsPDF: { unit: 'pt', format: 'a4', orientation: 'portrait' },
            pagebreak: { mode: ['css', 'legacy'], avoid: ['.row-wrapper', '.header', '.header-row', 'img'] }
        };

        html2pdf().set(options).from(element).output('blob').then(function (pdfBlob) {
            resolve(pdfBlob);
        }).catch(err => reject(err));
    });
}

async function generateChunkedReports() {
    const CHUNK_SIZE = 75; 
    let currentOffset = 0;
    let chunkNumber = 1;
    const MAX_CHUNKS = 150;
    
    const progressTracker = $('zip-progress-tracker');
    progressTracker.innerHTML = `Generating Reports... Please wait. A single ZIP file will download when finished.`;

    const today = new Date();
    const dateOnly = today.toISOString().slice(0, 10); 
    const zip = new JSZip(); 

    while (chunkNumber <= MAX_CHUNKS) {
        
        if (chunkNumber === 1) {
            $('dashboard-section').style.display = 'block';
            $('table-title').innerHTML = "No Gate Pass Vehicles";
        } else {
            $('dashboard-section').style.display = 'none';
            $('table-title').innerHTML = "No Gate Pass Vehicles (Continued)";
        }

        const rowsFetched = await get_history(currentOffset, CHUNK_SIZE, false, true);
        if (rowsFetched === 0 || rowsFetched === undefined) break; 
        
        await waitForImagesToLoad();
        const pdfBlob = await generatePDFBlob();
        
        zip.file(`system-report_${dateOnly}_part${chunkNumber}.pdf`, pdfBlob);
        progressTracker.innerHTML = `Generating Reports... Compiled part ${chunkNumber}. Please wait.`;
        
        if (rowsFetched < CHUNK_SIZE) break;
        currentOffset += CHUNK_SIZE;
        chunkNumber++;
    }
    
    $('dashboard-section').style.display = 'block';
    $('table-title').innerHTML = "No Gate Pass Vehicles";
    
    if (Object.keys(zip.files).length === 0) {
        progressTracker.innerHTML = "No data found to download.";
        return;
    }

    progressTracker.innerHTML = "Zipping files together...";
    
    zip.generateAsync({type:"blob"}).then(function(content) {
        saveAs(content, `System_Reports_${dateOnly}.zip`);
        progressTracker.innerHTML = "Download complete!";
        setTimeout(() => { progressTracker.innerHTML = ""; }, 5000);
        window.parent.postMessage('download_complete', '*');
    });
}

async function get_history(page_number=$('page_number') ? $('page_number').value : 0, per_page=12, getonly=false, isChunking=false) {
    let localFilters = localStorage.getItem('currentFilters');
    if (!localFilters) localFilters = filters.join(','); 
    let currentFilters = localFilters.split(',');

    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'get_history',
                    plate: currentFilters[0], status: currentFilters[1], vehicle_type: currentFilters[2],
                    gate_number: currentFilters[3], date_time: currentFilters[4], owner: currentFilters[5],
                    sort_by: currentFilters[6], sort_by_dir: currentFilters[7],
                    username: localStorage.getItem('current_user'), offset: page_number, limit: per_page
                }
            })
        });
        
        const result = await response.json();
        const table_content = $('table_content');
        table_content.innerHTML = ''; 
        
        let registered_count = 0; let not_registered_count = 0; let unidentified_count = 0;
        if (result.status === "success" && result.message[7]) {
            result.message[7].forEach(row => {
                if (row.status === "Registered") registered_count = row.count;
                else if (row.status === "Unidentifiable") unidentified_count = row.count;
                else not_registered_count += row.count; 
            });
        }
        let traffic_volume_labels = []; let entry_traffic_volume_values = []; let exit_traffic_volume_values = [];

        if (result.status === "success") {
            if(getonly==true) return result.message[0];
            console.log(result.message)
            
            result.message[0].forEach(element => {
                if (element['status']=="Registered") { /* registered_count+=1; */ } 
                else {
                    let wrapperNode = $make('div');
                    wrapperNode.className = 'row-wrapper';
                    
                    let rowNode = $make('div');
                    rowNode.className = 'div-row';
                    rowNode.innerHTML = row_builder(element);
                    
                    wrapperNode.appendChild(rowNode);
                    table_content.appendChild(wrapperNode);
                }
            });

            let entry_len = typeof(result.message[2]) == "string" ? 0 : result.message[2].length;
            let exit_len = typeof(result.message[3]) == "string" ? 0 : result.message[3].length;
            let traffic_volume_labels_count = entry_len < exit_len ? entry_len : exit_len;
            
            for (let item = 0; item < traffic_volume_labels_count; item++) {
                let entry_element = result.message[2][item]; let exit_element = result.message[3][item];
                traffic_volume_labels.push(traffic_volume_labels_count != exit_len ? entry_element['time'] : exit_element['time']);
                try { entry_traffic_volume_values.push(entry_element['count']); } catch { entry_traffic_volume_values.push(0); }
                try { exit_traffic_volume_values.push(exit_element['count']); } catch { exit_traffic_volume_values.push(0); }
            }

            let vehicle_classification_labels = []; let vehicle_classification_values = [];
            result.message[4].forEach(element => {
                vehicle_classification_labels.push(element['class']); vehicle_classification_values.push(element['count']);
            });

            let vehicles_today = parseInt(result.message[1][0]["total_transactions"]);
            $("VehiclesToday").innerHTML = vehicles_today;

            quick_metrics_chart.data.labels = [`Registered (${registered_count})`, `No Gate Pass (${not_registered_count})`, `Unidentified (${unidentified_count})`];
            quick_metrics_chart.data.datasets[0].data = [registered_count, not_registered_count, unidentified_count];
            quick_metrics_chart.update();

            traffic_volume_chart.data.labels = traffic_volume_labels;
            traffic_volume_chart.data.datasets[0].data = entry_traffic_volume_values;
            traffic_volume_chart.data.datasets[1].data = exit_traffic_volume_values;
            traffic_volume_chart.update();

            vehicle_classification_chart.data.labels = vehicle_classification_labels;
            vehicle_classification_chart.data.datasets[0].data = vehicle_classification_values;
            vehicle_classification_chart.update();

            let start_time = result.message[5][0]['first_entry'].split(' ')[0] + ' 7:00 AM';
            let end_time = result.message[5][0]['last_entry'].split(' ')[0] + ' 6:00 PM';
            $('report_duration').innerHTML = `(${start_time} - ${end_time})`;
            
            let employee_id = result.message[6][0]['employee_id'];
            let cur_date = result.message[6][0]['last_login'];
            $('user-name').innerHTML = `Employee ID ${employee_id}`;
            $('cur-date').innerHTML = `${cur_date}`;

            let status = currentFilters[1];
            let vehicle_type = currentFilters[2];
            let gate_number = currentFilters[3];
            let compiled_by = localStorage.getItem('current_user');
            
            if (gate_number=='1') { gate_number = 'entry camera'; }
            else if (gate_number=='2') { gate_number = 'exit camera'; }
            else { gate_number = 'entry and exit cameras'; }
            
            if (vehicle_type=='All') { vehicle_type='<u>all vehicle types</u>'; }
            else { vehicle_type='the type <u>'+vehicle_type+'</u>'; }

            let message = `A generated report of the summary of <u>${status}</u> vehicle records of ${vehicle_type} at the <u>${gate_number}</u> within the supervision of employee id <u>${compiled_by.toUpperCase()}</u>.`;
            message = message.toLowerCase(); 
            message = message.charAt(0).toUpperCase() + message.slice(1);
            $('intro').innerHTML = message;

            return result.message[0].length;

        } else {
            console.log(result.status + " message: " + result.message[0]);
            return 0;
        }
    } catch (error) {
        console.error("error:", error);
        return 0;
    }
}

window.onload = () => {
    if (window.self !== window.top) {
        generateChunkedReports();
    } else {
        get_history(0, 12, false, false);
    }
};