function updateStatus(data) {
    camera1_status = data.camera1_status 
    camera2_status = data.camera2_status 
    vehicles_today = data.vehicles_today
    not_registered_vehicles = data.not_registered_vehicles
    registered_vehicles = data.registered_vehicles
    unidentified_vehicles = data.unidentified_vehicles
    $('camera1-status-text').innerText = camera1_status;
    $('camera1-status-dot').setAttribute('status', camera1_status);
    $('camera2-status-text').innerText = camera2_status;
    $('camera2-status-dot').setAttribute('status', camera2_status);
}

var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
var dashboard_ws = new WebSocket(protocol + "//" + window.location.host + "/dashboard_ws");


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
        var message = JSON.parse(event.data);
        vehicles_today = message.vehicles_today;
        $("VehiclesToday").innerHTML = vehicles_today
        vehicle_classification_chart.data.labels = message.classification_labels;
        vehicle_classification_chart.data.datasets[0].data = message.classification_counts;
        vehicle_classification_chart.update();
        traffic_volume_chart.data.labels = message.camera1_traffic_volume_labels;
        traffic_volume_chart.data.datasets[0].data = message.camera1_traffic_volume_count;
        traffic_volume_chart.data.datasets[1].data = message.camera2_traffic_volume_count;
        traffic_volume_chart.update();
        quick_metrics_chart.data.labels = message.quick_metrics_labels;
        quick_metrics_chart.data.datasets[0].data = message.quick_metrics_count;
        quick_metrics_chart.update();
        updateStatus(message)
    } catch (error) {
        $('camera1-status-text').innerText = 'initializing';
        $('camera1-status-dot').setAttribute('status', 'initializing');
        $('camera2-status-text').innerText = 'initializing';
        $('camera2-status-dot').setAttribute('status', 'initializing');
    }
}

Chart.defaults.color = '#000';
const qm_ctx = $('quick_metrics_chart').getContext('2d');
const quick_metrics_chart = new Chart(qm_ctx, {
    type: 'pie',
    data: {
        labels: ['Registered', 'No Gate Pass', 'Unidentifiable'],
        datasets: [{
            label: 'Vehicle Count',
            data: [0, 0, 0], 
            backgroundColor: [
                'rgba(43, 163, 45, 1)',
                'rgba(235, 14, 31, 1)',
                'rgba(255, 191, 38, 1)'
            ],
            borderColor: [
                'rgba(43, 163, 45, 0)',
                'rgba(235, 14, 31, 0)',
                'rgba(255, 191, 38, 0)'
            ],
      borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
            },
            datalabels: {
                formatter: (value, qm_ctx) => {
                    let sum = 0;
                    let dataArr = qm_ctx.chart.data.datasets[0].data;
                    dataArr.map(data => {
                        sum += data;
                    });
                    
                    if (value === 0) {
                        return null;
                    }
                    
                    let percentage = (value * 100 / sum).toFixed(2) + "%";
                    return percentage;
                },
                color: '#000',
            },
            tooltip: {
                enabled: true
            }
        }
    },
    plugins: [ChartDataLabels]
});

const vcc_ctx = $('vehicle_classification_chart').getContext('2d');
const vehicle_classification_chart = new Chart(vcc_ctx, {
    type: 'bar',
    data: {
        labels: ['Tricycle', 'Car', 'Motorcycle'],
        datasets: [{
            label: '',
            data: [0, 0, 0], 
            backgroundColor: [
                '#F47982',
                '#1A74A3',
                '#FCD657'
            ]
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                    },
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            datalabels: {
                formatter: (value, vcc_ctx) => {
                    let sum = 0;
                    let dataArr = vcc_ctx.chart.data.datasets[0].data;
                    dataArr.map(data => {
                        sum += data;
                    });
                    
                    if (value === 0) {
                        return null;
                    }
                    
                    let percentage = value;
                    return percentage;
                },
                color: '#000',
            },
            tooltip: {
                enabled: false
            }
        }
    },
    plugins: [ChartDataLabels]
});

const tv_ctx = $('traffic_volume_chart').getContext('2d');
curve = 0
const traffic_volume_chart = new Chart(tv_ctx, {
    type: 'line',
    data: {
        labels: [0],
        datasets: [
            {
                label: 'Entry Traffic',
                data: [0], 
                fill: true,
                backgroundColor: 'rgba(12,75,5,0.3)',
                borderColor: '#0C4B05',
                borderWidth: 2,
                pointRadius: 1.25,
                lineTension: curve
            },
            {
                label: 'Exit Traffic',
                data: [0], 
                fill: true,
                backgroundColor: 'rgba(12,5,75,0.3)',
                borderColor: '#0C054B',
                borderWidth: 2,
                pointRadius: 1.25,
                lineTension: curve
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            datalabels:{
                display: false
            },
            tooltip: {
                enabled: true 
            }
        },
        scales: {
            x: {
                grid: {
                    display: false,
                    min: -1
                }
            },
            y: {
                grid: {
                    // display: false
                },
                display: true,
                min: 0,
                grace: '10%'
            }
        }
    },
    plugins: [ChartDataLabels]
});