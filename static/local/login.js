// $listen("keypress", function(event) {
//     if (event.keyCode == 13) {
//         handleLogin();
//     }
// });
$listen('keyup', (event) => {
    if (event.key === 'Enter') {
        if($('popup_div')==null) {
            handleLogin();
        }
    }
});
let lf = null
function lastfocused(element) {
    lf = element
}
async function handleLogin() {
    const uid_input = $('login_employee_id');
    const password_input = $('login_password');
    const uid = uid_input.value;
    const password = password_input.value;


    if (!uid && !password) {
        await popup("Employee ID and Password cannot be empty!","message",() => {uid_input.focus()})
        return
    }
    if (!uid) {
        await popup("Employee ID cannot be empty!","message",() => {uid_input.focus()})
        return
    }
    if (!password) {
        await popup("Password cannot be empty!","message",() => {password_input.focus()})
        return
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userid: uid,
                password: password
            })
        });

        const result = await response.json();

        if (result.status === "success") {
            localStorage.removeItem('lastOpenedTab');
            localStorage.setItem('current_role',result.message['role'])
            localStorage.setItem('current_user',uid)
            window.location.href = "/main";
        } else {
            // alert(result.message);
            await popup(result.message,"message");
            lf.focus();
        }
    } catch (error) {
        console.error("Login error:", error);
        // alert("Could not connect to the server.");
        await popup("Could not connect to the server.","message");
    }
}