function handle_search_enter(event) {
    if (event.key === 'Enter') {
        get_users()
    }
}
function content_builder(user_info,with_controls) {
    const user_id = user_info['employee_id']
    const username = user_info['name']
    const role = user_info['role']
    const active = user_info['active']
    const options = {   weekday: 'short', 
    year: 'numeric', 
                        month: 'short', 
                        day: 'numeric', 
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                    };
    const last_login = user_info['last_login'].split('T').join(' ')
    const formatted_last_login = new Intl.DateTimeFormat('en-GB', options).format(new Date(last_login))
    let formatted_last_logout = "N/A"
    if (user_info['last_logout']!=null) {
        const last_logout = user_info['last_logout'].split('T').join(' ')
        formatted_last_logout = new Intl.DateTimeFormat('en-GB', options).format(new Date(last_logout))
    }
    if (active==1) {
        formatted_last_logout = "Currently Active"
    }
    // const formatted_last_logout = new Intl.DateTimeFormat('en-GB', options).format(new Date(last_logout))
    let template = `  <td>${user_id}</td>
                        <td>${username}</td>
                        <td>${role}</td>
                        <td>${formatted_last_login}</td>
                        <td>${formatted_last_logout}</td>`
    if (with_controls==true) {
        template += `
                        <td>
                            <div style="width: 95%; margin-right: 20px;display: flex;justify-content: end;gap:10px;">
                                <a class="button green" href="/edit_user" onclick="edit_user('${user_id}')">Edit</a>
                                <a class="button red" style="padding-left: 10px; padding-right: 10px;" href="/reset_password" onclick="edit_user('${user_id}')">Reset Password</a>
                            </div>
                        </td>`
    }
    else {
        template += `<td></td>`
    }
    return template
}
async function display_users(users) {
    const users_table = $('table_content')
    users.forEach(user => {
        if (user['employee_id']==localStorage.getItem('current_user')) {
            localStorage.setItem('current_role',user['role'])
        }
    })
    users_table.innerHTML = ''
    users.forEach(user => {
        let add_controls = false
        let content = $make('tr')
        if (user['employee_id']==localStorage.getItem('current_user') || localStorage.getItem('current_role')=="ADMIN") {
            add_controls = true
        }
        content.innerHTML = content_builder(user,add_controls)
        users_table.appendChild(content)
    });
}
get_users()
async function get_users() {
    $('table_content').innerHTML = ''
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'users',
                    search: $('searchInput').value
                }
            })
        });

        const result = await response.json();

        if (result.status === "success") {
            await display_users(result.message)
        } else {
            console.log(result.status + " message: " + result.message);
        }
    } catch (error) {
        console.error("Login error:", error);
        alert("Could not connect to the server.");
    }
}

function edit_user(user_id) {
    localStorage.setItem("edit_user_id",user_id)
}