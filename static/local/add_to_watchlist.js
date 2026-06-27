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
            await top.popup(`Added ${plate} to watchlist successfully!`, 'message')
            window.location.href = '/notifications'
        }
        else {
            console.log("error:", result.message);
            if (result.message.includes('Duplicate entry')) {
                await top.popup(`The plate ${plate} is already in the watchlist.`)
            }
        }
    } catch (error) {
        console.log("error:", error);
    }
}