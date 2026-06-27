function handle_cancel() {
    window.location.href = localStorage.getItem("lastOpenedTab")
}
function isOnlyNumbers(input) {
    return /^\d+$/.test(input);
}
function isOnlyLetters(input) {
    return /^[a-zA-Z]+$/.test(input);
}
const fileInput = $('pfp');
fileInput.addEventListener('change', (event) => {
const file = event.target.files[0];
const maxSize = 10 * 1024 * 1024;
read_file()
async function read_file() {
    if (file) {
        if (file.size > maxSize) {
        await top.popup("File is too large! Maximum allowed size is 10MB.","message")
        input.value = "N/A";
        return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
        const result = e.target.result;
        $('user_icon').src = result;
        };
        reader.readAsDataURL(file); 
    }
}
});


$('user_id').innerHTML = localStorage.getItem('edit_user_id')
$('employee_id').value = localStorage.getItem('edit_user_id')
if(localStorage.getItem('current_role')!="ADMIN"){
    $('role_div').innerHTML = ''
}
handle_edit_user_info()
async function handle_edit_user_info() {
    try {
        const response = await get_user_info(localStorage.getItem('edit_user_id'));
        const result = await response.json();
        if (result.status === "success") {
            const content = result.message[0]
            let email = content['email']
            let name = content['name']
            let role = content['role']
            let pfp = content['pfp']

            if (email=='') {
                email = 'N/A'
            }
            if (name=='') {
                name = 'N/A'
            }
            if (role=='') {
                role = 'N/A'
            }
            if (pfp!='N/A') {
                $('user_icon').src = pfp
            }

            $('username').innerHTML = name
            $('user_email').innerHTML = email
            $('user_role').innerHTML = role
            $('employee_name').value = name
            $('employee_email').value = email
            $('employee_role').value = role
        } else {
            console.log(result.status + " message: " + result.message);
        }
    } catch (error) {
        console.log(`Edit User error: ${error}`)
    }
}

async function save_edit_user_changes() {
    
    let target = localStorage.getItem('edit_user_id')
    let employee_id = $('employee_id').value
    let employee_name = $('employee_name').value
    let employee_email = $('employee_email').value
    let pfp = $('user_icon').src
    let employee_role = "Security Guard"

    // intercept dagijy maid nga input dtuy
    const empIdArray = employee_id.split("-")
    if (empIdArray.length != 2 || !isOnlyLetters(empIdArray[0]) || !isOnlyNumbers(empIdArray[1])) {
        await popup("Invalid Employee ID format!","message",() => {$('employee_id').focus()})
        return
    }
    const empEmailArray = employee_email.split("@")
    if ((empEmailArray.length !=2 || 
        !empEmailArray[1].includes('.') || 
        empEmailArray[1].split('.').includes('') ||
        empEmailArray[0].split('.').includes('') ||
        empEmailArray[0][0] == '.') && employee_email!='N/A') {
        await popup("Invalid Email format!","message",() => {$('employee_email').focus()})
        return
    }

    if (localStorage.getItem('current_role')=="ADMIN") {
        employee_role =  $('employee_role').value;
    }

    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'set_user_info',
                    target: target,
                    id: employee_id,
                    name: employee_name,
                    email: employee_email,
                    role: employee_role,
                    pfp: pfp
                }
            })
        });
        
        const result = await response.json();
        if (result.status === "success") {
            await top.popup("Changes saved successfully!", "message")
            if (localStorage.getItem('current_user')==target) {
                localStorage.setItem('current_user',employee_id)
                localStorage.setItem('current_role',employee_role)
            }
            window.top.location.reload();
        } else {
            console.log(result.message)
            console.log(result.message.includes('Duplicate entry'))
            console.log(result.message.includes('employee_id'))
            if (result.message.includes('Duplicate entry') && result.message.includes('employee_id')) {
                const emp_id = $('employee_id').value;
                await top.popup(`Employee ID ${emp_id} is already in use!`, 'message');
            }
            if (result.message.includes('No rows were affected')) {
                // Simulate good save
                await top.popup("Changes saved successfully!", "message")
                if (localStorage.getItem('current_user')==target) {
                    localStorage.setItem('current_user',employee_id)
                    localStorage.setItem('current_role',employee_role)
                }
                window.top.location.reload();
            }
            console.log(result.status + " message: " + result.message);
        }
    } catch (error) {
        console.log(`Edit User error: ${error}`)
    }

}

async function delete_user() {
    let confirmed = false
    let target = localStorage.getItem('edit_user_id')
    if (localStorage.getItem('current_user')==target) {
        await top.popup(
            "You are deleting your OWN account! Are you sure?",
            "confirm",
            confirm_fxn = () => {confirmed=true},
            "Delete"
        )
    }
    else {
        await top.popup(`You are deleting ${target}\`s account permanently! Are you sure?`,"confirm",() => {confirmed=true})
    }
    if (!confirmed) {
        return
    }

    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'delete_user',
                    target: target,
                }
            })
        });
        
        const result = await response.json();
        if (result.status === "success") {
            await top.popup("User deleted successfully!","message")
            if (localStorage.getItem('current_user')==target) {
                window.top.location.href = "/login";
            }
            else {
                window.location.href = "/users";
            }
        } else {
            console.log(result.status + " message: " + result.message);
        }
    } catch (error) {
        console.log(`Edit User error: ${error}`)
    }

}