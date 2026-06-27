//////////////////////////////////////////////////////
max_page_index = 0;
item_per_page = 14;
current_page_index = 0;
//////////////////////////////////////////////////////
function gotopage(event, page) {
  if (event.key === "Enter") {
    go_to_page(page - 1);
    $('current_page').value = ''
  }
}

function handle_search_enter(event) {
  if (event.key === "Enter") {
    handle_search();
  }
}

function handle_search() {
  current_page_index = 0;
  renderTable(last_received_message, true);
}

function go_to_next_page() {
  new_page = current_page_index + 1;
  if (new_page < max_page_index) {
    current_page_index = new_page;
    localStorage.setItem(
      "current_live_video_page_index",
      current_page_index,
    );
    renderTable(last_received_message, true);
  }
}
function go_to_prev_page() {
  new_page = current_page_index - 1;
  if (new_page >= 0) {
    current_page_index = new_page;
    localStorage.setItem(
      "current_live_video_page_index",
      current_page_index,
    );
    renderTable(last_received_message, true);
  }
}

function go_to_page(page) {
  if (page >= 0 && page < max_page_index) {
    current_page_index = page;
    localStorage.setItem("current_live_video_page_index", page);
    renderTable(last_received_message, true);
  }
}
last_status_filter_index = parseInt(localStorage.getItem('current_live_video_filter'))
status_filter_index = last_status_filter_index >= 0 || last_status_filter_index <=3 ? parseInt(localStorage.getItem('current_live_video_filter')):0;
filters = ["All", "No Gate Pass", "Registered", "Unidentifiable"];
function toggleStatusFilter(inc) {
  status_filter_index = (status_filter_index + inc) % 4;
  localStorage.setItem('current_live_video_filter',status_filter_index)
  let filter_span = $("status_filter");
  filter_span.innerText = `(${filters[status_filter_index]})`;
  current_page_index = 0;
  renderTable(last_received_message, true);
}
let debug = false;
let graphs = false;
if (localStorage.getItem("debug_mode") !== null) {
  debug = JSON.parse(localStorage.getItem("debug_mode"));
}
if (localStorage.getItem("graphs") !== null) {
  graphs = JSON.parse(localStorage.getItem("graphs"));
}

$listen("keydown", function (event) {
  if (event.ctrlKey) {
    if (event.shiftKey) {
      if (event.key === "b" || event.key === "B") {
        event.preventDefault();
        debug = !debug;
        localStorage.setItem("debug_mode", JSON.stringify(debug));
        renderTable(last_received_message);
        sendDataToPython({
          data: {
            debug: debug,
            purpose: "toggle_debug",
          },
        });
        location.reload()
      }
    }
    else if (event.key === "b" || event.key === "B") {
      event.preventDefault();
      debug = !debug;
      localStorage.setItem("debug_mode", JSON.stringify(debug));
      renderTable(last_received_message);
      location.reload()
    }
    else if (event.key === "g" || event.key === "G") {
      event.preventDefault();
      graphs = !graphs;
      localStorage.setItem("graphs", JSON.stringify(graphs));
      renderTable(last_received_message);
      sendDataToPython({
        data: {
          graphs: graphs,
          purpose: "toggle_graphs",
        },
      });
      // location.reload()
    }
  }
});

let top_id = ''
$listen('keyup',(event)=>{
  if (event.key==" ") {
    $(top_id).click()
  }
})

var protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
var live_video_ws = new WebSocket(
  protocol + "//" + window.location.host + "/live_video_ws",
);
refresh_table()
function refresh_table() {
  var firstOpen = setInterval(function() {
      if (live_video_ws.readyState === WebSocket.OPEN) {
          live_video_ws.send("Send data please!!");
          clearInterval(firstOpen)
      }
      else {
          console.log("Connection not ready yet!")
      }    
  },50)
}



let table = $("table_content");
let placeholder_table = $("table_placeholders");
const target_table_rows = item_per_page;

let last_received_message = null;
let master_data = {};
toggleStatusFilter(0)
if (localStorage.getItem("current_live_video_page_index") != null) {
  current_page_index = parseInt(
    localStorage.getItem("current_live_video_page_index"),
  );
}
function renderTable(message, force_refresh = false) {
  
  if (!message) return;
  
  if (!force_refresh && message.new_data && Object.keys(message.new_data).length === 0) {
      return;
  }

  if (message.new_data) {
      Object.assign(master_data, message.new_data);
  }
  
  last_received_message = { new_data: master_data };
  try {
    var ascending_data = master_data;
    var new_data = Object.fromEntries(
      Object.entries(ascending_data).reverse(),
    );
    var keys = Object.keys(new_data);
    
    var search_query = $("search_bar").value.toLowerCase();

    var filtered_keys = keys.filter(key => {
      let camera1 = new_data[key];
      let plate = (camera1.plate || "").toLowerCase();
      let owner = (camera1.owner || "").toLowerCase();
      let vehicle_status = camera1.status;
      let confirmed = camera1.confirmed;

      if (search_query && !plate.includes(search_query) && !owner.includes(search_query)) {
        return false;
      }
      current_status_filter = filters[status_filter_index]
      if (current_status_filter == "Unidentifiable") {
        return plate=='' || confirmed != true;
      } else {
        if (current_status_filter != "All" && current_status_filter != vehicle_status) {
          return false;
        }
        if (current_status_filter == "No Gate Pass" && confirmed == false) {
          return false;
        }
      }
      return true;
    });
    max_page_index = Math.ceil(filtered_keys.length / item_per_page);
    if (current_page_index >= max_page_index && max_page_index > 0) {
        current_page_index = max_page_index - 1;
    }

    $("current_page").placeholder = current_page_index + 1;
    $("current_page").value = current_page_index + 1;
    $("current_page").max = max_page_index || 1;
    $("max_page").innerHTML = max_page_index || 1;

    let start_index = current_page_index * item_per_page;
    let end_index = Math.min(start_index + item_per_page, filtered_keys.length);
    let target_row_ids = filtered_keys.slice(start_index, end_index);

    for (let i = table.rows.length - 1; i >= 0; i--) {
      if (!target_row_ids.includes(table.rows[i].id)) {
        table.deleteRow(i);
      }
    }

    for (let o = start_index; o < end_index; o++) {
      if (o==start_index) {
        top_id = filtered_keys[o] 
      } 
      let key = filtered_keys[o];
      let index_on_page = o - start_index;
      let fkey = o < item_per_page*(current_page_index+1) - 1 ? filtered_keys[o + 1] : key;
      let pkey = o > item_per_page*(current_page_index) ? filtered_keys[o - 1] : key;
      
      let camera1 = new_data[key];
      let plate = camera1.plate;
      let date = camera1.date;
      let locrs = camera1.ocrs;
      let ttd = camera1.text_to_display;
      let method = camera1.method;
      let new_detection = camera1.visible;
      let owner_names = camera1.owner.toLowerCase().split(" ");
      for (let i = 0; i < owner_names.length; i++) {
        let indiv_letters = owner_names[i].split("");
        if (indiv_letters[0] != undefined) {
          indiv_letters[0] = indiv_letters[0].toUpperCase();
          let new_name = indiv_letters.join("");
          owner_names[i] = new_name;
        }
      }
      
      if (!debug) {
        method = "";
        new_data[key]['ocrs'] = null
        new_data[key]['method'] = ''
      }
      let owner = owner_names.join(" ");
      if (owner == "N/a") {
        owner = "N/A";
      }
      let vehicle_status = camera1.status;
      let time = camera1.time;
      let vehicle_type = camera1.vehicle_type;
      let confirmed = camera1.confirmed;

      let camera_names = { camera1: "Entrance", camera2: "Exit" };
      let camera_location = camera_names[key.split("-")[0]];
      let content = "";
      const options = { 
        weekday: 'short',
        year: 'numeric',
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      };
      
      const formatted_date = new Intl.DateTimeFormat('en-US', options).format(new Date(`${camera1.date} ${camera1.time}`))
      
      const click_function = () => {
        let plate_display = `${plate}`
        if (display_status=='Unidentifiable') {
          plate_display = ''
        }
        top.manual_verification(
          key, 
          fkey,
          pkey,
          new_data[key],
        )
      }
      
      let display_status = `${ttd} &#x1F50E;&#xFE0E;`;
      if (plate!='' && confirmed == true) {
        display_status = vehicle_status
        content = `
                          <td><plate onmouseup="event.stopPropagation()" method="${method}">${plate}</plate></td>
                          <td status="${vehicle_status}" colspan="1" style="text-align:center;">
                            ${vehicle_status}
                          </td>
                          <td>${owner}</td>
                          <td>${vehicle_type}</td>
                          <td>${camera_location}</td>
                          <td>${formatted_date}</td>
                          `;
      }
      else {
        display_status = `Unidentifiable`;
        content = `
                          <td status="Unidentifiable" colspan="3" style="text-align:center;">
                            ${display_status}
                          </td>
                          <td>${vehicle_type}</td>
                          <td>${camera_location}</td>
                          <td>${formatted_date}</td>
                          `;
      }

      let existing_row = $(key);
      if (existing_row) {
        if (existing_row.innerHTML !== content) {
          existing_row.innerHTML = content;
          existing_row.className = vehicle_status;
          existing_row.classList.add('clickable');
          existing_row.onclick = click_function;
        }
        if (table.rows[index_on_page] !== existing_row) {
          table.insertBefore(existing_row, table.rows[index_on_page]);
        }
      } else {
        let tr = $make("tr");
        tr.id = key;
        tr.className = vehicle_status;
        tr.classList.add('clickable');
        tr.innerHTML = content;
        tr.onclick = click_function;
        if (index_on_page >= table.rows.length) {
          table.appendChild(tr);
        } else {
          table.insertBefore(tr, table.rows[index_on_page]);
        }
      }
    }
    add_table_placeholders();
    
    let log_div = $("log_table");
    const tolerance = 50;
    const isScrolledToBottom =
      log_div.scrollHeight - log_div.clientHeight <=
      log_div.scrollTop + tolerance;
    if (isScrolledToBottom) {
      log_div.scrollTop = log_div.scrollHeight;
    }
  } catch (error) {
    console.log(error);
  }
}

live_video_ws.onmessage = function (event) {
  renderTable(JSON.parse(event.data));
};

add_table_placeholders();
function add_table_placeholders() {
  placeholder_table.innerHTML = "";
  for (
    let additional_rows = 0;
    additional_rows < target_table_rows - table.rows.length;
    additional_rows++
  ) {
    placeholder_table.innerHTML =
      placeholder_table.innerHTML +
      `<tr class="placeholderTR"><td></td><td></td><td></td><td></td><td></td><td></td></tr>`;
  }
}
function removeExcessRow() {
  const table = $("table_content");
  if (table && table.rows.length > item_per_page) {
    table.deleteRow(item_per_page);
    return true;
  } else {
    return false;
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