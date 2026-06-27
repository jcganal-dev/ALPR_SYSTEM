function popup(message,type,confirm_fxn=null,confirm_text="confirm", controls_align = 'center', text_align = 'center') {
    return new Promise((resolve) => {
        container_style = `
            position: fixed;
            top: 0;
            left: 0;
            display: flex;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            z-index: 3;
            flex-direction: column;
            align-items: center;
            justify-content: center;`
        message_cont_style = `
            display: flex;
            max-width: 350px;
            width: auto;
            min-width: 250px;
            height: auto;
            background-color: rgb(255, 255, 255);
            border-radius: 5px;
            color: black;
            flex-direction: column; 
            align-items: center;
            justify-content: center;
            gap:25px;
            padding: 15px 10px 20px 10px;
            `
        normal_button = `
            text-decoration: none;
            color: white;
            background-color: #ffffff;
            padding: 3px 8px;
            cursor: pointer;
            border: 2px outset black;
            border-radius: 4px;
            color: black;
        `
        green_button = `
            text-decoration: none;
            color: white;
            background-color: #186907;
            padding: 3px 8px;
            cursor: pointer;
            border-radius: 4px;
        `
        red_button = `
            text-decoration: none;
            color: white;
            background-color: #E80A0A;
            padding: 3px 8px;
            cursor: pointer;
            border: 2px outset #9a0707;
            border-radius: 4px;
        `
        let okay_button = $make('a');
        okay_button.innerHTML = "Okay"
        okay_button.style = normal_button
        okay_button.onclick = function() {
            $('popup').remove();
            resolve();
            if (confirm_fxn) confirm_fxn();
        };
        let confirm_button = $make('a');
        confirm_button.innerHTML = confirm_text
        confirm_button.style = red_button
        confirm_button.onclick = function() {
            $('popup').remove();
            resolve();
            if (confirm_fxn) confirm_fxn();
        };
        let controls = $make("div")
        controls.append(okay_button)
        if (type=="confirm") {
            controls = $make("div")
            okay_button.innerHTML = "Cancel"
            okay_button.onclick = function() {
                $('popup').remove();
                resolve();
            };
            controls.append(okay_button)
            controls.append(confirm_button)
        }
        controls.style = `display:flex;flex-direction:row;gap:10px;justify-content: ${controls_align}; align-items: ${controls_align}; width: 100%;`
        let message_element = $make('div')
        message_element.innerHTML = message
        message_element.style = `text-align:${text_align};`

        let container = $make('div');

        let message_container = $make('div'); 
        message_container.style = message_cont_style
        message_container.id = "popup_div"

        
        message_container.append(message_element)
        message_container.append(controls)
        container.append(message_container)
        container.style = container_style
        container.id = 'popup'
        document.body.appendChild(container)
        container.setAttribute('tabindex', '-1');
        container.style.outline = 'none';
        container.focus();
        container.addEventListener("keyup", (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (event.key === "Enter") {
                if (type === "confirm") {
                    confirm_button.click();
                } else {
                    okay_button.click();
                }
            }
            if (event.key === "Escape") {
                okay_button.click();
            }
            document.getElementById('iframe').contentDocument.event.target.focus()
        });
    })
}

function notify(message, type, fnx = null) {
    let prefix = `<strong>Notification</strong>`;
    if (type === 'warning') {
        prefix = `<label class="blinking warnign-emoji">⚠️</label><strong>Warning!</strong>`;
    }

    let container = $('notification-bar');
    if (!container) {
        container = $make('div');
        container.className = 'notification-bar';
        container.id = 'notification-bar';
        document.body.appendChild(container);
    }
    let card = $make('div');
    card.className = 'notif-container';

    gate = ""

    if (message[2] == '1') {
        gate = " at the Entrance Camera"
    }
    if (message[2] == '2') {
        gate = " at the Exit Camera"
    }

    const options = {
        weekday: 'short',
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    const formatted_last_login = new Intl.DateTimeFormat('en-US', options).format(new Date(message[1]))
    card.innerHTML = `  
        <notifheader>
            <label class="notif-title">LPR System</label>
            <a class="button" id="close-notif" style="margin-top: -2px; cursor: pointer;">🞬</a>
        </notifheader>
        <notifTitle>
            ${prefix}
        </notifTitle>
        <notifBody>
            <label id="message">Watchlist vehicle ${message[0]} has been detected within the premises${gate}.</label>
            <label id="date" style="margin-top:5px">${formatted_last_login}</label>
        </notifBody>
        <notiffooter>
            <a class="boxed-button" onclick="navigate_to('notifications');clear_notifications()" style="margin-top: -2px; cursor: pointer;">See Watchlist</a>
        </notiffooter>
    `;

    let close_button = card.querySelector('#close-notif');
    close_button.onclick = function() {
        let activeContainer = $('notification-bar');
        if (activeContainer) {
            if (activeContainer.childElementCount > 1) {
                card.remove();
            } else {
                activeContainer.remove();
            }
        }
    };

    container.appendChild(card);
}
let current_ocrs = []
function manual_verification(key, fkey, pkey, current_data) {
    const plate = current_data['plate'] || current_data['plate_number']
    const method = current_data['method'] || ""
    const list_ocrs = current_data['ocrs'] || []
    current_ocrs = list_ocrs
    let ocrs = [];
    if (list_ocrs.length != 0) {
        ocrs.push(`<li>Readings:</li>`);
        for (let p = 0; p < list_ocrs.length; p++) {
            if (list_ocrs[p] != "") {
            ocrs.push(`<li>${list_ocrs[p]}</li>`);
            }
        }
        ocrs = ocrs.join("");
    }
    if (method == null) {
        method = "Failed to read plate or find a match";
    }
    const owner = current_data['owner'] || current_data['full_name']
    const display_status = current_data['status']
    const vehicle_type = current_data['vehicle_type'] 
    const plate_display = plate == "" || plate == undefined ? "" : `<plate>${plate}</plate>`;
    const camera_names = { camera1: "Entrance", camera2: "Exit" };
    const camera_location = camera_names[key.split("-")[0]];
    const options = { 
        weekday: 'short',
        year: 'numeric',
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    let formatted_date = current_data['date_time']
    if (formatted_date==null) {
        formatted_date = new Intl.DateTimeFormat('en-US', options).format(new Date(`${current_data['date']} ${current_data['time']}`))
    }


    container = $make('div');
    container.id = 'floating_dark_bg';
    container.className = 'floating-dark-bg'
    container.tabIndex = '-1'
    content = `
      <card width="700px">
        <card-header>
          <label class="title">Manual Verification</label>
          <div class="X-button no-select" id="x_button" onclick="document.getElementById('${container.id}').remove();document.getElementById('iframe').contentDocument.getElementById('main-container').focus()">
            <div>🞬</div>
          </div>
        </card-header>
        <card-content>
          <card-image-container>
            <div id="plate_title"><plate>${plate}</plate></div>
            <div class="image_details_container">
              <div id="image_details" style="padding:5px;">
                <label status='${display_status}'>${display_status}</label> ${vehicle_type} ${plate_display}<br>Location: ${camera_location} camera <br>${formatted_date}
              </div>
            </div>
            <img src="/images/${key}.png" id="floating_image_display_conf" onerror="imageFallback(this)" alt="Image not found! Please report as a bug."/>
            <img src="/images/${key}--snap.png" id="floating_image_display" onerror="imageFallback(this)" alt="Image not found! Please report as a bug."/>
            <img src="/images/${key}--mbae.png" id="floating_image_display_mbae" onerror="imageFallback(this)" alt="Image not found! Please report as a bug."/>
          </card-image-container>
          <input type="hidden" value="${key}" id="id_container" />
          <card-actions>
            <div style="font-size: 20px">Enter Details Manually</div>
            <div class="input_group_div">
              <label>Plate Number:</label>
              <input type="text" oninput="input_to_upper(this);" id="plate_input"/>
            </div>
            <div style="justify-content: space-between; display: flex">
              <a class="red_button" onclick="top.popup('Are you sure you want to delete this record?<br>Plate: <strong>${plate || 'N/A'}</strong><br>Owner: <strong>${owner}</strong>', 'confirm', () => {handle_delete_record();},confirm_text='Delete',controls_align='end', text_align='start')">
                <img src="static/images/trash.png" class="trash_icon">Delete Record
              </a>
              <a class="button1 verify-button" onclick="verify_record()">
                Verify
              </a>
            </div>
            <div style="border: 1px solid"></div>
            <div style="justify-content: space-between; display: none">
                <a class="button1 verify-button" id="prev_button" onclick="document.getElementById('x_button').click();document.getElementById('iframe').contentWindow.document.getElementById('${pkey}').click()">
                < Prev
                </a>
                <a class="button1 verify-button" id="next_button" onclick="document.getElementById('x_button').click();document.getElementById('iframe').contentWindow.document.getElementById('${fkey}').click()">
                Next >
                </a>
            </div>
            <div id="results_div"></div>
            <label>${method}</label>
            <ul id="ocrs_div">${ocrs}</ul>
          </card-actions>
        </card-content>
        <input type="hidden" id="target_plate" value="${plate}" />
        <input type="hidden" id="target_name" value="${owner}" />
        <input type="hidden" id="vehicle_type" value="${vehicle_type}" />
      </card>`
    container.innerHTML = content
    document.body.appendChild(container)
    $('plate_input').focus()
}

$listen('keyup',(event) => {
    if (event.key == 'ArrowRight') {
        $('next_button').click()
    }
    else if (event.key == 'ArrowLeft') {
        $('prev_button').click()
    }
})


async function simulate() {
    const checkPromises = current_ocrs.map((plate, index) => check_registration(plate, index === 4?'true':'false'));
    const results = await Promise.all(checkPromises);
    let found_match = false;
    const plate_input_value = $('plate_input').value
    $('ocrs_div').innerHTML = ''
    console.log(results)
    $('ocrs_div').innerHTML += `<li>Readings:</li>`
    results.forEach(result => {
        found_match = found_match || (result['registered'] && plate_input_value.trim()==result['reading'])
        $('ocrs_div').innerHTML += `<li>${result['original']}${(result['registered'] && plate_input_value.trim()==result['reading'])==true?` - Found! (${result['reading']})</li>`:'</li>'}`
    });
    if (!found_match) {
        $('ocrs_div').innerHTML += `<li>Failed to read!</li>`
    }
    $('ocrs_div').innerHTML += `<li><a id='verify_button' style="text-decoration: none; color: white; background-color: #186907; padding: 3px 8px 3px 8px;cursor:pointer;border-radius:5px;" onclick="location.reload()">Done</a></li>`
}

async function check_registration(plate,use_adv_patt) {
    console.log(plate.split(' into ')[0])
    return sendDataToPython({
        data: {
            purpose: "simulate",
            plate_text: plate.split(' into ')[0],
            use_advance_patterns: 'true',
        },
    });
}