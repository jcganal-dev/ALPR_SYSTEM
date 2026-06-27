$listen("keyup", (event) => {
if (event.key === "Escape") {
        $("floating_dark_bg").remove();
        $('iframe').contentDocument.getElementById('main-container').focus()
    }
});
$listen("keyup", (event) => {
    if (event.key === "Enter") {
        if ($("verify_button") != null) {
            // $("verify_button").click();
        } else {
            verify_record();
        }
    }
});

let timeouts = []
function showControls(element) {
    element.style.opacity = '1';
    element.parentElement.children[1].style.filter = 'brightness(100%)';
    element.style.cursor = 'default';
    timeouts.forEach(loop => {
        if (element==loop[1]) {
            clearTimeout(loop[0]);
        }
    });
    let timeout = setTimeout(function(){
        element.style.opacity = '0';
        element.parentElement.children[1].style.filter = 'brightness(100%)';
        element.style.cursor = 'none';
    },1000)
    timeouts.push([timeout,element])
}
function toggleBtn(Btn,input) {
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
    Btn.firstElementChild.src = type === 'password' ? '/static/images/hidden.png' : '/static/images/eye.png';
    input.focus();
}
function input_to_upper(input) {
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const originalLength = input.value.length;
    input.value = input.value.toUpperCase().replace(/\s/g, '');
    const diff = originalLength - input.value.length;
    input.setSelectionRange(start - diff, end - diff);
}
function imageFallback(element) {
    element.style.display = 'none';
}

function display_results(result) {
    plate_text = result["original"];
    vehicle_type = result["vehicle_type"];
    registered = "No Gate Pass";
    if (result["registered"] == true) {
        registered = "Registered";
    }
    owner_names = result["owner"].toLowerCase().split(" ");
    for (let i = 0; i < owner_names.length; i++) {
        indiv_letters = owner_names[i].split("");
        if (indiv_letters[0] != undefined) {
            indiv_letters[0] = indiv_letters[0].toUpperCase();
            new_name = indiv_letters.join("");
            owner_names[i] = new_name;
        }
    }
    owner = owner_names.join(" ");
    if (owner == "N/a") {
        owner = "N/A";
    }
    id = $("id_container").value;
    $("results_div").innerHTML = `
    <div style="border: solid 1px black; display:flex;flex-direction:column; align-items:center; gap:10px;padding:0px 0px 5px 0px;">
        <table style="width: 100%;">
            <thead><th colspan='2'>Results:</th></thead>
            <tbody>
                <tr>
                    <th>Plate</th><td>${plate_text}</td>
                </tr>
                <tr>
                    <th>Status</th><td status="${registered}">${registered}</td>
                </tr>
                <tr>
                    <th>Owner</th><td>${owner}</td>
                </tr>
            </tbody>
        </table>
        <div style="display: flex; gap: 10px;">
            <a id='verify_button' onclick="
                        sendDataToPython({'data': {
                            'id':'${id}',
                            'plate_text':'${plate_text}',
                            'status':'${registered}',
                            'owner':'${owner}',
                            'vehicle_type':'${vehicle_type}',
                            'purpose':'confirm'
                        }});
            " style="text-decoration: none; color: white; background-color: #186907; padding: 3px 8px 3px 8px;cursor:pointer;border-radius:5px;">
                Save
            </a>
            <a id='add_to_database_button' onclick="
                        sendDataToPython({'data': {
                            'id':'${id}',
                            'plate_text':'${plate_text}',
                            'status':'${registered}',
                            'owner':'${owner}',
                            'vehicle_type':'${vehicle_type}',
                            'purpose':'add_to_database'
                        }});
            " style="text-decoration: none; color: white; background-color: #186907; padding: 3px 8px 3px 8px;cursor:pointer;border-radius:5px;">
                Simulate
            </a>    
        </div>
    </div>`;
}
async function get_user_info(uid) {
    return await fetch('/api/get_from_database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            data: {
                purpose: 'get_user_info',
                uid: uid
            }
        })
    });
}
async function handle_shutdown() {
    await popup(
        'Confirm Shutdown', 
        'confirm', 
        () => {sendDataToPython({'data': {'purpose':'shutdown'}});},
        confirm_text = 'Shutdown'
    )
}
async function handle_logout_and_shutdown() {
    await popup(
        'Confirm Shutdown', 
        'confirm', 
        confirm_fxn = async () => {
            await logout();
            await sendDataToPython({'data': {'purpose':'shutdown'}});
        },
        confirm_text = 'Shutdown'
    )
}
async function delete_record() {
    let id = $("id_container").value;
    sendDataToPython({
        data: {
            id: id,
            purpose: "delete",
        },
    });
}
function verify_record() {
    let plate_text = $("plate_input").value.trim();
    let vehicle_type = $("vehicle_type").value.trim();
    if (plate_text.length > 0) {
        sendDataToPython({
            data: {
                plate_text: plate_text,
                vehicle_type: vehicle_type,
                purpose: "verify",
            },
        });
    }
}