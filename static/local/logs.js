///////////////////////////////////////////
const default_perpage = 13;
///////////////////////////////////////////

$listen('mouseup', (event) => {
    let selectedText = window.getSelection().toString();
    if (!selectedText && document.activeElement && document.activeElement.tagName === 'INPUT') {
        const activeInput = document.activeElement;
        selectedText = activeInput.value.substring(activeInput.selectionStart, activeInput.selectionEnd);
    }
    if (selectedText.trim().length > 0) {
        event.stopPropagation()
    }
}, true);

let top_id = ''
$listen('keyup',(event)=>{
  if (event.key==" ") {
    $(top_id).click()
  }
})

function handle_page_input(element) {
    if (parseInt(element.value) > parseInt(element.max)) {
        element.value = element.max;
    }
    if (parseInt(element.value) < 1) {
        element.value = 1
    }
    go_to_page(element.value-1)
    let currentpage = $('current_page').value;
    if (currentpage.trim()=='') {
        currentpage = $('current_page').placeholder;
    }
    localStorage.setItem('currentVehicleLogsPage', currentpage);
}

window.onload = () => {
    page_before = parseInt(localStorage.getItem("currentVehicleLogsPage"))
    go_to_page(page_before-1)
}

let jd = true;
async function handle_search() {
    if (!jd) {return}
    jd = false;
    filters[5] = $('search_bar').value;
    if (!$('search_bar').value || $('search_bar').value == '') {
        filters[5] = 'All';
    }
    await get_history();
    jd = true;
}

function handle_search_enter(event) {
    if (event.key === 'Enter') {
        handle_search()
    }
}

function download_logs() {
    const status = $('download_status');
    const icon = $('download_icon');
    status.innerHTML = '<span class="spinner"></span> Preparing report...';
    status.style.display = 'inline-block';
    status.style.color = 'gray';
    icon.style.opacity = '0.5';
    icon.style.pointerEvents = 'none';
    $('download_icon').parentElement.style.display = 'none';
    $('template_download').src='/report_template'
}

window.addEventListener('message', function(event) {
    if (event.data === 'download_complete' || event.data === 'download_error') {
        const status = $('download_status');
        const icon = $('download_icon');
        if (event.data === 'download_complete') {
            status.innerHTML = '✅ Done';
            status.style.color = 'white';
        } else {
            status.innerHTML = '❌ Error';
            status.style.color = 'white';
        }
        $('download_icon').parentElement.style.display = 'inline-block';
        setTimeout(function(){
            status.innerHTML = "Download Report"
            icon.style.opacity = '1';
            icon.style.pointerEvents = 'auto';
            $('template_download').src = '';
        }, 3000);
    }
});

function handle_date_input(from, to) {
    if (!to.value || to.value<from.value) {
        to.value = from.value
    }
    if (!from.value) {
        from.value = to.value
    }
    filters[4]=`${from.value} to ${to.value}`;
    $('current_page').value = 1;
    get_history()
}

function toggle_custom_date(show) {
    const custom_date_container = $('custom_date_container');
    if (show==true) {
        custom_date_container.style.display = 'flex'
    }
    else {
        custom_date_container.style.display = 'none'
    }
}

function gotopage(event, page) {
    if (event.key === "Enter") {
        go_to_page(page - 1);
        $('current_page').value = ''
        localStorage.setItem('currentVehicleLogsPage', page);
    }
}

function go_to_next_page() {
    let current_p = parseInt($('current_page').placeholder) - 1;
    let max_p = parseInt($('max_page').innerHTML);
    if (current_p + 1 < max_p) {
        $('current_page').value = current_p + 2;
        go_to_page(current_p + 1);
    }
    localStorage.setItem('currentVehicleLogsPage', current_p + 2);
}

function go_to_prev_page() {
    let current_p = parseInt($('current_page').placeholder) - 1;
    if (current_p > 0) {
        go_to_page(current_p - 1);
        $('current_page').value = current_p;
        localStorage.setItem('currentVehicleLogsPage', current_p);
    }
}

function go_to_page(page) {
    if (page==-1) {
        page = 0
    }
    get_history(page * default_perpage);
}

async function handle_delete_record() {
    await delete_record()
    await top.popup("Vehicle record deleted successfully.", 'message')
    $("floating_dark_bg").remove();
    go_to_page(parseInt(localStorage.getItem("currentVehicleLogsPage"))-1)
}

filters = ['All', 'All', 'All', 'All', 'Today', 'All', 'date_time', 'DESC']
function row_builder(row) {
    let gate_name = ['Entrance','Exit']
    let full_name = row['full_name'] || ''
    let plate_number_val = row['plate_number']
    let guard_on_duty = row['guard_on_duty']
    if (guard_on_duty == null) {
        guard_on_duty = "N/A"
    }
    let plate_display = plate_number_val != '' ? `<plate>${plate_number_val}</plate>` : ''
    let inner_content  = `
            <td>${plate_display}</td>
            <td status='${row['status']}'>${row['status']}</td>
            <td>${full_name}</td>`
    if (row['status']=='Unidentifiable') {
        inner_content = `<td status='${row['status']}' colspan="3" style="text-align:center;">${row['status']}</td>`
    }
    return `
            ${inner_content}
            <td>${row['vehicle_type']}</td>
            <td>${gate_name[row['gate_number']-1]}</td>
            <td>${row['date_time']}</td>
            <td>${guard_on_duty}</td>
            `;
}

async function get_history(page_number=0,per_page=default_perpage,getonly=false) {
    localStorage.setItem('currentFilters',filters)
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'get_history',
                    plate: filters[0],
                    status: filters[1],
                    vehicle_type: filters[2],
                    gate_number: filters[3],
                    date_time: filters[4],
                    owner: filters[5],
                    sort_by: filters[6],
                    sort_by_dir: filters[7],
                    username: localStorage.getItem('current_user'),
                    offset: page_number,
                    limit: per_page
                }
            })
        });
        
        const result = await response.json();
        const table_content = $('table_content')
        table_content.innerHTML = ''
        if (result.status === "success") {
            if(getonly==true) {
                return result.message[0];
            }
            just_started = true
            console.log(result.message[0])
            result.message[0].forEach((element, index) => {
                const options = {
                    weekday: 'short',
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                };
                if (just_started) {
                    top_id = `row_${index}`
                    just_started = false
                }
                const location = element['gate_number'] == 1 ? 'Entrance' : 'Exit';
                const formatted_last_login = new Intl.DateTimeFormat('en-US', options).format(new Date(element['date_time']))
                element['date_time'] = formatted_last_login
                let tr = $make('tr')
                tr.id = `row_${index}`;
                tr.innerHTML = row_builder(element)
                tr.classList.add('clickable');
                console.log(element)

                let pkey = index > 0 ? `row_${index-1}` : `row_${index}`
                let fkey = index+1 < per_page ? `row_${index+1}` : `row_${index}`
                
                tr.onclick = () => {
                    let id = element['transaction_id']; 
                    if (element['full_name']==null) {
                        element['full_name'] = "N/A"
                    }
                    let plate = element['plate_number']
                    if (element['plate_number'].split('').length < 1) {
                        plate = "Unidentifiable"
                    }
                    // top.manual_verification(id, plate, "", "", element['full_name'], element['status'], element['vehicle_type'], element['status'], location, element['date_time'], fkey, pkey)
                    top.manual_verification(id, fkey, pkey, element)
                };
                table_content.appendChild(tr)
            });
        let vancant_row = per_page - result.message[0].length
        for (let i = 0;i<vancant_row;i++) {
            let placeholder = $make('tr')
            placeholder.appendChild($make('td'))
            placeholder.appendChild($make('td'))
            placeholder.appendChild($make('td'))
            placeholder.appendChild($make('td'))
            placeholder.appendChild($make('td'))
            placeholder.appendChild($make('td'))
            placeholder.appendChild($make('td'))
            placeholder.style.height = '46px'
            table_content.appendChild(placeholder)
        }
        let mpn = parseInt(result.message[1][0]["total_transactions"]);
        let max_page_idx = Math.ceil(mpn / default_perpage);
        let current_page_idx = Math.floor(page_number / default_perpage);
            
        $('current_page').placeholder = current_page_idx + 1;
        $('current_page').max = max_page_idx || 1;
        $('max_page').innerHTML = max_page_idx || 1;
        } else {
            $('current_page').placeholder = 1;
            $('max_page').innerHTML = 1;
            console.log(result.status + " message: " + result.message[0]);
        }
    } catch (error) {
        console.error("Logs error:", error);
    }
}

$listen('keyup', (event) => {
  if (event.key=='ArrowLeft') {
    go_to_prev_page()
  }
  else if (event.key=='ArrowRight') {
    go_to_next_page()
  }
})