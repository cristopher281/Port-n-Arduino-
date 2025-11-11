const socket = io();

let chart;
const MAX_POINTS = 120;
let labels = [];
let dataPoints = [];
let movPoints = [];

function createChart(){
  const ctx = document.getElementById('chart').getContext('2d');
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Distancia (cm)',
        data: dataPoints,
        borderColor: '#00e5ff',
        backgroundColor: 'rgba(0,229,255,0.04)',
        tension: 0.2,
        pointRadius: 2
      }, {
        label: 'Movimiento',
        data: movPoints,
        type: 'scatter',
        pointRadius: 6,
        pointBackgroundColor: '#ff5c7c'
      }]
    },
    options: {
      animation: false,
      responsive: true,
      scales: {
        x: { display: true },
        y: { beginAtZero: true }
      }
    }
  });
}

socket.on('connect', ()=>{
  console.log('Conectado al servidor');
});

socket.on('sensor', (d)=>{
  // d: {dist, mov}
  const t = new Date().toLocaleTimeString();
  labels.push(t);
  dataPoints.push(d.dist);
  // Para scatter, añadimos objeto con x=index, y=value (Chart.js scatter uses x/y)
  if(d.mov){
    movPoints.push({x: labels.length-1, y: d.dist});
  }
  if(labels.length>MAX_POINTS){ labels.shift(); dataPoints.shift();
    // ajustar movPoints: eliminar los que queden fuera
    movPoints = movPoints.filter(p => p.x > labels.length-1 - MAX_POINTS);
    // reindex movPoints x para el chart (simple solución: remap to new indices)
    movPoints = movPoints.map((p,i)=>({x: p.x - 1, y: p.y}));
  }
  document.getElementById('dist').textContent = d.dist + ' cm';
  document.getElementById('mov').textContent = d.mov ? '¡DETECTADO!' : 'NO';
  chart.update('none');
});

function sendCmd(pos){
  socket.emit('command', {angle: pos});
}

createChart();
