async function sendDataToPython(dataObject) {
    try {
        const response = await fetch('/api/send_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dataObject)
        });

        if (response.ok) {
            const result = await response.json();
            purpose = dataObject['data']['purpose']
            if (purpose=='shutdown') {
                console.log("Suttinfdown")
                sendDataToPython({'data': {
                    'purpose':'kill'
                }});
            }
            if (purpose=='verify') {
                display_results(result)
            }
            if (purpose=='toggle_debug') {
                debug = dataObject['data']['debug']
                sendDataToPython({'data': {
                    'purpose':purpose,
                    'debug':debug
                }});
            }
            if (purpose=='confirm') {
                
            }
            if (purpose=='add_to_database') {
                simulate()
            }
            if (purpose=='simulate') {
                return result
            }
            if (purpose=='get_configs') {
                return result
            }
        } else {
            console.error('Failed to send data to server. Respose:', response);
        }
    } catch (error) {
        console.error('Error sending data:', error);
    }
}