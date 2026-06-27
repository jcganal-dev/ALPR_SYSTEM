// $listen("keypress", function(event) {
//     if (event.keyCode == 13) {
//         handleRegister();
//     }
// });

$listen('keyup', (event) => {
    if (event.key === 'Enter') {
        if($('popup_div')==null) {
            handleRegister();
        }
    }
});

function isOnlyNumbers(input) {
  return /^\d+$/.test(input);
}
function isOnlyLetters(input) {
  return /^[a-zA-Z]+$/.test(input);
}
async function handleRegister() {
    const empId_input = $('register_employee_id');
    const username_input = $('register_name');
    const password_input = $('register_password');
    const confirm_input = $('register_confirm_password');
    const empId = empId_input.value.trim();
    const username = username_input.value;
    const password = password_input.value;
    const confirm = confirm_input.value;

    if (!username) {
        await popup("Name cannot be empty!","message",() => {username_input.focus()})
        return
    }
    if (!empId) {
        await popup("Employee ID cannot be empty!","message",() => {empId_input.focus()})
        return
    }
    const empIdArray = empId.split("-")
    if (empIdArray.length != 2 || !isOnlyLetters(empIdArray[0]) || !isOnlyNumbers(empIdArray[1])) {
        await popup("Invalid Employee ID format!","message",() => {empId_input.focus()})
        return
    }
    if (!password) {
        await popup("Password cannot be empty!","message",() => {password_input.focus()})
        return
    }
    if (!confirm) {
        await popup("Confirm Password cannot be empty!","message",() => {confirm_input.focus()})
        return
    }
    
    if (password !== confirm) {
        await popup("Passwords are not the same!","message",() => {confirm.focus()})
        return;
    }

    // if (!isOnlyNumbers(empId)) {
    //     popup("Employee ID can only contain numbers!","message",() => {empId_input.focus()})
    //     return;
    // }

    const response = await fetch('/api/register_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            userid: empId,
            username: username, 
            password: password
        })
    });

    const result = await response.json();
    // alert(result.message);
    if (result.status === "success") {
        await popup("Account created successfully! Please login.","message");
        window.location.href = "/login";
    }
    else {
        await popup(result.message,"message");
    }
}