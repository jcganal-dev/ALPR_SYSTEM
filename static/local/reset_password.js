$('user_id').innerHTML = localStorage.getItem('edit_user_id')
handle_reset_password_user_info()
async function handle_reset_password_user_info() {
    try {
        const response = await get_user_info(localStorage.getItem('edit_user_id'))
        const result = await response.json();
        if (result.status === "success") {
            const content = result.message[0]
            console.log(content)
            let email = content['email']
            let pfp = content['pfp']
            let name = content['name']
            let role = content['role']

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
        // alert("Could not connect to the server.");
    }
}

async function save_reset_password_changes() {      
    let target = localStorage.getItem('edit_user_id')
    let password = $('password').value
    let confirm_password = $('confirm_password').value
    if (!password) {
        $('password').style.borderColor = 'red'
        $('password').focus()
        $('password_error').innerHTML = "Please type your new password."
        $('password_error').style.visibility = 'unset'
        return
    }
    if (password!=confirm_password) {
        $('confirm_password').style.borderColor = 'red'
        $('confirm_password').focus()
        $('confirm_password_error').innerHTML = "Passwords must be identical!"
        $('confirm_password_error').style.visibility = 'unset'
        return
    }
    try {
        const response = await fetch('/api/get_from_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: {
                    purpose: 'set_user_password',
                    target: target,
                    password: password
                }
            })
        });
        const result = await response.json();
        if (result.status === "success") {
            await top.popup('Changes saved successfully!','message')
            window.location.href = "/users";
        } else {
            console.log(result.status + " message: " + result.message);
            if (result.message.includes('No rows were affected')) {
                await top.popup('New password cannot be the same as the old password','message')
            }
        }
    } catch (error) {
        console.log(`Reset Password error: ${error}`)
    }

}

function inputting(input, error) {
    input.value = input.value.replace(/\s/g, '')
    input.style.borderColor = '#186907'
    error.innerHTML = 'No error.'
    error.style.visibility = 'hidden'
}