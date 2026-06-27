let current_active = "dashboard";
navigate_to(localStorage.getItem('lastOpenedTab'),system_set=true)

window.addEventListener('DOMContentLoaded', (event) => {
    console.log(localStorage.getItem('current_user'))
    if (localStorage.getItem('current_user')==null) {
        window.location.href='/login'
    }
});

function navigate_to(id,system_set) {
    if ($(id)==null) {
        id = "dashboard"
    }

    if (localStorage.getItem('lastOpenedTab')==id && !system_set) {
        return
    }

    $("user-name").innerHTML = localStorage.getItem('current_user');
    $(current_active).classList.remove("active");
    $(id).classList.add("active");
    $("iframe").src = "/"+id;
    current_active = id
    localStorage.setItem("lastOpenedTab", current_active)
}

handle_main_user_info()
async function handle_main_user_info() {
    try {
        const response = await get_user_info(localStorage.getItem('current_user'))
        
        const result = await response.json();
        if (result.status === "success") {
            const content = result.message[0]
            console.log(content)
            let pfp = content['pfp']
            if (pfp!='N/A') {
                $('user_icon').src = pfp
                $('user_icon').onclick = () => {
                    localStorage.setItem("edit_user_id",content['employee_id']);
                    $('iframe').src= '/edit_user'
                }
            }

        } else {
            console.log(result.status + " message: " + result.message);
        }
    } catch (error) {
        // alert("Could not connect to the server.");
    }
}

async function handle_delete_record() {
  await delete_record();
  await top.popup("Vehicle record deleted successfully.", 'message');
  $("floating_dark_bg").remove();
  $("iframe").contentWindow.location.reload()
}

let sidebar_expanded = false;
function handle_sidebar(icon) {
    if (!sidebar_expanded) {
        $("side-bar").classList.add('side-bar-open');
        sidebar_expanded = !sidebar_expanded
        icon.style.transform = 'rotateY(0deg)';
    }
    else {
        $("side-bar").classList.remove('side-bar-open');
        sidebar_expanded = !sidebar_expanded
        icon.style.transform = 'rotateY(180deg)';
    }
}

function clear_notifications() {
    if ($('notification-bar')!=null) {
        $('notification-bar').remove()
    }
}

var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
var dashboard_ws = new WebSocket(protocol + "//" + window.location.host + "/notifications_ws");
window.onload = function() {
    var firstOpen = setInterval(function() {
        if (dashboard_ws.readyState === WebSocket.OPEN) {
            dashboard_ws.send("Send data please!!");
            clearInterval(firstOpen)
        }
        else {
            console.log("Connection not ready yet!")
        }    
    },50)
}

dashboard_ws.onmessage = function(event) {
    try {
        data = JSON.parse(event.data)
        message = data['message']
        type = data['type']
        if (message=="Notification Test") {
            return
        }
        console.log(message)
        notify(message,type,()=>{$('notifications').click()})
    } catch (error) {
        console.log(error)
    }
}

async function handle_logout() {
    await popup(
        'Confirm Logout', 
        'confirm', 
        confirm_fxn = () => {logout()},
        confirm_text = 'Logout'
    )
}

async function logout(silent=false) {
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'logout_user',
                    target: localStorage.getItem('current_user')
                }
            })
        });
        
        const result = await response.json();
        if (result.status === "success") {
            window.location.href = '/login'
            localStorage.clear();
        } else {
            if (!silent) {
                popup(result.status + " message: " + result.message, "message");
            }
        }
    } catch (error) {
        if (!silent) {
            popup("Logout failed! Server error.", "message");
        }
    }
}