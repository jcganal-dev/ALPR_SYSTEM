const default_perpage = 6 ;
function handle_date_input(from, to) {
    if (!to.value || to.value<from.value) {
        to.value = from.value
    }
    if (!from.value) {
        from.value = to.value
    }
    filters[4]=`${from.value} to ${to.value}`;
    $('page_number').value = 1;
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
function build_page_button(current,max_page) {
    if (current < 1) current = 1
    let page_container = $('page_prev')
    page_container.innerHTML = ''
    let visible = current + 2
    let start = current - 3
    if (visible<6) {visible = 6}
    if (visible>max_page) {visible = max_page}
    if (start<1) {start = 1}
    if (current<max_page-3){
        for (let i = start; i <= max_page; i++) {
            if (i < visible || i == max_page || max_page-visible==1) {
                if (i==start) {
                    let page = $make('a')
                    page.onclick = () => scroll_hist(i)
                    page.innerHTML = "<<"
                    page.style.cursor = 'pointer'
                    page_container.appendChild(page)
                }
                let page = $make('a')
                page.onclick = () => scroll_hist(i)
                page.innerHTML = i
                page.style.cursor = 'pointer'
                if (i==current) {page.classList.add('verify-button')}
                page_container.appendChild(page)
                if (i==max_page) {
                    let page = $make('a')
                    page.onclick = () => scroll_hist(i)
                    page.innerHTML = ">>"
                    page.style.cursor = 'pointer'
                    page_container.appendChild(page)
                }
            }
            else if(max_page-visible>1) {
                let page = $make('span')
                page.innerHTML = '...'
                page_container.appendChild(page)
                i+=max_page-visible-1
            }
        }
    }
    else {
        for (let i = 1; i <= max_page; i++) {
            if (i == 1 || i > max_page - 5) {
                if(i==1) {
                    let page = $make('a')
                    page.onclick = () => scroll_hist(i)
                    page.innerHTML = "<<"
                    page.style.cursor = 'pointer'
                    page_container.appendChild(page)
                }
                let page = $make('a')
                page.onclick = () => scroll_hist(i)
                page.innerHTML = i
                page.style.cursor = 'pointer'
                if (i==current) {page.classList.add('verify-button')}
                page_container.appendChild(page)
                if(i==max_page) {
                    let page = $make('a')
                    page.onclick = () => scroll_hist(i)
                    page.innerHTML = ">>"
                    page.style.cursor = 'pointer'
                    page_container.appendChild(page)
                }
            }
            else {
                let page = $make('span')
                page.innerHTML = '...'
                page_container.appendChild(page)
                i=max_page-5
            }
        }
    }
}
function scroll_hist(dir) {
    offset = default_perpage
    if (dir == 'prev') {
        offset = -default_perpage
    }
    else if (dir == 'next') {
        offset = default_perpage
    }
    else offset = null
    dest = parseInt($('page_number').value) + parseInt(offset)
    if (!offset) {
        dest=parseInt((dir-1)*default_perpage)
    }
    if (dest<0) dest = 0
    // alert(dest + ' >= ' + (parseInt($('max_page_number').value)))
    if (dest>=parseInt($('max_page_number').value)) dest = $('page_number').value
    $('page_number').value = dest;
    get_history(dest)
}
async function process_new_entry(plate,reason,user) {
    if (plate.trim()=='') {
        popup('Plate number cannot be empty!', 'message')
        return
    }
    if (reason.trim()=='') {
        reason = "None"
    }
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'add_watchlist_entry',
                    plate: plate,
                    reason: reason,
                    user: user
                }
            })
        });
        const result = await response.json();
        if (result.status=="success") {
            location.reload()
        }
    } catch (error) {
        // console.error("error:", error);
        // alert("Could not connect to the server.");
    }
}
async function remove_entry(plate) {
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'remove_watchlist_entry',
                    plate: plate
                }
            })
        });
        const result = await response.json();
        console.log(plate)
        console.log(result)
        if (result.status=="success") {
            await top.popup("Watchlist record deleted successfully.", 'message')
            location.reload()
        }
    } catch (error) {
        // console.error("error:", error);
        // alert("Could not connect to the server.");
    }
}
function row_builder(row) {
    gate_name = ['Entrance','Exit']
    if (row['last_name']==null) {
        row['last_name']=''
    }
    if (row['first_name']==null) {
        row['first_name']=''
    }
    full_name = row['first_name'] + " " + row['last_name']
    if (row['last_name']=='' && row['first_name']=='') {
        full_name = 'N/A'
    }
    plate_number = row['plate_number']
    if (plate_number != '') {
        plate_number = `<plate>${row['plate_number']}</plate>`
    }
    if (row['vehicle_type']==null) {
        row['vehicle_type'] = "N/A"
        if (row['vehicle_model']==null) {
            row['vehicle_model'] = "N/A"
        }
        row['vehicle_type'] = row['vehicle_model']
    }
    if (row['status']==null) {
        row['status'] = "N/A"
    }
    console.log(row['formatted_date'])
    if (row['formatted_date']==null) {
        row['formatted_date'] = "N/A"
    }
    else {
        const options = {   weekday: 'short', 
                            year: 'numeric', 
                            month: 'short', 
                            day: 'numeric', 
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: true
                        };
        row['formatted_date'] = new Intl.DateTimeFormat('en-GB', options).format(new Date(row['formatted_date']))
    }
    
    saved_picture = row['saved_picture']
    if (row['formatted_date']=="N/A") {
        saved_picture = "N/A"
    }
    // content = `
    //     <td><img src="${saved_picture.slice(1)}" class="vehicle_preview" onerror="this.src='/static/images/image_not_found.png'"></td>
    //     <td>${plate_number}</td>
    //     <td status='${row['status']}'>${row['status']}</td>
    //     <td>${full_name}</td>
    //     <td>${row['vehicle_type']}</td>
    //     <td>${gate_name[row['gate_number']-1]}</td>
    //     <td>${row['formatted_date']}</td>`
    content = `
        <td>
            <div style="width:100%; display:flex; justify-content:center;">
                <img src="${saved_picture}" class="vehicle_preview" onerror="this.src='/static/images/image_not_found.png'">
            </div>
        </td>
        <td>
            <div style="display:flex;flex-direction:column;gap:10px">
                <span>Owner: ${full_name}</span>
                <span>Plate Number: ${plate_number}</span>
                <span>Vehicle Type: ${row['vehicle_type']}</span>
                <span>Status: <label status="${row['status']}">${row['status']}</label></span>
            </div>
        </td>
        <td>
            <div style="display:flex;flex-direction:column;gap:10px;height:100px;">
                <div style="display:flex;flex-direction:row;justify-content:stretch;">
                    <div style="display:flex;flex-direction:column;width:60%;">
                        <span>Last detection: ${row['formatted_date']}</span>
                        <span>Location: ${gate_name[row['gate_number']-1]}</span>
                    </div>
                    <div>
                        <span>Added to watchlist by: ${row['added_by']}</span>
                    </div>
                </div>
                <span>Remarks: ${row['remarks']}</span>
            </div>
        </td>
        <td>
            <div style="margin-left:40px;display:flex;flex-direction:column;gap:20px; justify-content:center;">
                <span><a class='red_button' style="width: fit-content;" onclick="top.popup('This watchlist entry will be PERMANENTLY deleted! Are you sure?', 'confirm', confirm_fxn = () => {remove_entry('${row['plate_number']}')}, confirm_text = 'Remove')"><img src="static/images/trash.png" class="trash_icon"> Delete</a></span>
            </div>
        </td>
        `
    return content
}
// console.log(get_history(page_number=0, per_page=default_perpage))

watchlist = []
get_watchlist()
async function get_watchlist() {
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'get_watchlist_list'
                }
            })
        });
        const result = await response.json();
        console.log(result.message)
        result.message.forEach(element => {
            plate_number = element['plate_number']
            added_by = element['added_by']
            remarks = element['remarks']
            watchlist.push({plate_number,added_by,remarks})
        });
    } catch (error) {
        // console.error("error:", error);
        // alert("Could not connect to the server.");
    }
    get_history()
}
async function get_history() {
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'get_for_watchlist',
                    watchlist: watchlist
                }
            })
        });
        const result = await response.json();
        const table_content = $('table_content')
        table_content.innerHTML = ''
        if (result.status === "success") {
            result.message.forEach(element => {
                let td = $make('tr')
                console.log(element[0])
                td.innerHTML = row_builder(element[0])
                table_content.appendChild(td)
            });
        // let vancant_row = per_page - result.message[0].length
        // for (let i = 0;i<vancant_row;i++) {
        //     let placeholder = $make('tr')
        //     placeholder.appendChild($make('td'))
        //     placeholder.appendChild($make('td'))
        //     placeholder.appendChild($make('td'))
        //     placeholder.appendChild($make('td'))
        //     placeholder.appendChild($make('td'))
        //     placeholder.appendChild($make('td'))
        //     placeholder.appendChild($make('td'))
        //     placeholder.style.height = '47px'
        //     table_content.appendChild(placeholder)
        // }
        } else {
            console.log(result.status + " message: " + result.message[0]);
        }
    } catch (error) {
        // console.error("error:", error);
        // alert("Could not connect to the server.");
    }
}