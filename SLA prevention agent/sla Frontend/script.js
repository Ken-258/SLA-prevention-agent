document.addEventListener('DOMContentLoaded', () => {

    const API_URL = 'http://127.0.0.1:8080';

    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('incidentTableBody');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotMessages = document.getElementById('chatbotMessages');
 
    loadDashboardMetrics();
    loadIncidentTable();

    async function loadDashboardMetrics() {
        try {
            const response = await fetch(`${API_URL}/metrics/summary`);
            if (!response.ok) throw new Error('Network response was not ok');
            const metrics = await response.json();

            document.getElementById('total-incidents').textContent = metrics.total_tickets;
            document.getElementById('high-priority').textContent = metrics.by_priority.High || 0;
            document.getElementById('medium-priority').textContent = metrics.by_priority.Medium || 0;
            document.getElementById('low-priority').textContent = metrics.by_priority.Low || 0;

            const slaRate = metrics.sla_achievement_rate_pct;
            document.getElementById('sla-percentage').textContent = `${slaRate}%`;

            const donutChart = document.getElementById('sla-donut-chart');
            if (donutChart) {
                donutChart.style.background = `conic-gradient(var(--high-prio-color) 0% ${slaRate}%, var(--low-prio-color) ${slaRate}% 100%)`;
            }
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    async function loadIncidentTable(endpoint = '/tickets') {
        try {
            const response = await fetch(`${API_URL}${endpoint}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            const tickets = data.tickets || data.results || [];
            tableBody.innerHTML = '';

            if (tickets.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No incidents found.</td></tr>';
                return;
            }
            
            let unassignedCount = 0;

            tickets.forEach(ticket => {
                const hoursLeft = Number(ticket.hours_left) || 0;
                const totalSeconds = Math.floor(hoursLeft * 3600);

                const row = document.createElement('tr');
                row.dataset.status = ticket.status;

                if (ticket.status === 'breached') row.classList.add('breached');
                if (ticket.status === 'at-risk') row.classList.add('at-risk');
                if ((ticket.assigned_to || 'Unassigned').toLowerCase() === 'unassigned') unassignedCount++;

                const estHours = Math.abs(Math.floor(hoursLeft * 2)) || 1;

                row.innerHTML = `
                    <td>${ticket.id}</td>
                    <td>${ticket.title}</td>
                    <td><span class="prio-tag ${(ticket.priority || 'low').toLowerCase()}">${ticket.priority || 'Low'}</span></td>
                    <td class="time-breach" data-time="${totalSeconds}">...</td>
                    <td>~ ${estHours} hours</td>
                    <td>${ticket.assigned_to || 'Unassigned'}</td>
                    <td><button class="complete-btn">Mark as Done</button></td>
                `;
                tableBody.appendChild(row);
            });
            
            document.getElementById('unassigned-incidents').textContent = unassignedCount;
            addCompleteButtonListeners();
            updateBreachTimes(); 

        } catch (error) {
            console.error('Error loading tickets:', error);
            tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Error loading data.</td></tr>';
        }
    }

    let countdownInterval;
    function updateBreachTimes() {
        if (countdownInterval) clearInterval(countdownInterval);
        countdownInterval = setInterval(() => {
            const timeCells = document.querySelectorAll('.time-breach');
            timeCells.forEach(cell => {
                let totalSeconds = parseInt(cell.getAttribute('data-time'), 10);
                if (isNaN(totalSeconds)) return;

                totalSeconds--;
                cell.setAttribute('data-time', totalSeconds);

                const isNegative = totalSeconds < 0;
                const absSeconds = Math.abs(totalSeconds);
                const hours = Math.floor(absSeconds / 3600);
                const minutes = Math.floor((absSeconds % 3600) / 60);
                const seconds = absSeconds % 60;
                
                const formattedTime = `${isNegative ? '-' : ''}${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                cell.textContent = formattedTime;
                cell.classList.toggle('time-breached', isNegative);
            });
        }, 1000);
    }

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.trim();
        if (searchTerm) {
            loadIncidentTable(`/search?q=${encodeURIComponent(searchTerm)}`);
        } else {
            loadIncidentTable('/tickets');
        }
    });

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.getAttribute('data-filter');
            if (filter === 'all') loadIncidentTable('/tickets');
            else loadIncidentTable(`/tickets?status=${filter}`);
        });
    });

    chatbotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userInput = chatbotInput.value.trim();
        if (userInput === '') return;

        addMessage(userInput, 'user');
        chatbotInput.value = '';

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userInput })
            });
            const data = await res.json();
            addMessage(data.response, 'bot');
        } catch (err) {
            console.error(err);
            addMessage(" Unable to connect to SLA backend.", 'bot');
        }
    });

    window.addEventListener('load', async () => {
        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'menu' })
            });
            const data = await res.json();
            addMessage(data.response, 'bot');
        } catch {
            addMessage(" Unable to connect to backend. Please start the Flask server.", 'bot');
        }
    });

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        let lines = [];
        if (typeof text === 'string' && text.match(/\r?\n/)) {
            lines = text.split(/\r?\n/).filter(Boolean);
        } else if (typeof text === 'string') {
           
            lines = text.split(/(?<=[.!?])\s+/).filter(Boolean);
        } else {
        
            lines = [String(text)];
        }

       
        lines.forEach((line) => {
            const lineEl = document.createElement('div');
            lineEl.textContent = line.trim();
            messageDiv.appendChild(lineEl);
        });

        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    
    function addCompleteButtonListeners() {
        const completeBtns = document.querySelectorAll('.complete-btn');
        completeBtns.forEach(btn => {
            if (btn.dataset.listener) return;
            btn.dataset.listener = true;
            btn.addEventListener('click', (e) => {
                const row = e.target.closest('tr');
                row.classList.add('completed');
                row.dataset.status = 'completed';
                e.target.disabled = true;
                e.target.textContent = 'Completed';
            });
        });
    }

});
