document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');

    async function loadDashboard() {
        const response = await fetch('/dashboard/data', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) { alert('Ошибка загрузки данных'); return; }
        const data = await response.json();

        // Обновляем баланс
        document.getElementById('balance').innerText = data.balance.toFixed(2);

        // Обновляем таблицу транзакций
        const tableBody = document.getElementById('transactionTable');
        tableBody.innerHTML = '';
        data.transactions.forEach(t => {
            const tr = document.createElement('tr');
            tr.dataset.id = t.id;
            tr.innerHTML = `
                <td>${t.date}</td>
                <td>${t.type === 'income' ? 'Доход' : 'Расход'}</td>
                <td>${t.category || '-'}</td>
                <td>${t.description || ''}</td>
                <td>${t.amount.toFixed(2)}</td>
                <td><button class="deleteBtn">Удалить</button></td>
            `;
            tableBody.appendChild(tr);
        });

        // Обновляем категории
        const categorySelect = document.getElementById('categorySelect');
        categorySelect.innerHTML = '<option value="">Выберите категорию</option>';
        data.categories.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.innerText = c.name;
            categorySelect.appendChild(opt);
        });

        // Удаление транзакций
        document.querySelectorAll('.deleteBtn').forEach(btn => {
            btn.addEventListener('click', async e => {
                const id = e.target.closest('tr').dataset.id;
                const resp = await fetch(`/dashboard/delete_transaction/${id}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (resp.ok) loadDashboard();
            });
        });
    }

    // Добавление транзакции
    document.getElementById('transactionForm').addEventListener('submit', async e => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        data.amount = parseFloat(data.amount);

        const response = await fetch('/dashboard/add_transaction', {
            method: 'POST',
            headers: { 'Content-Type':'application/json','Authorization': `Bearer ${token}` },
            body: JSON.stringify(data)
        });

        if(response.ok) {
            e.target.reset();
            loadDashboard();
        } else {
            alert('Ошибка при добавлении транзакции');
        }
    });

    // Добавление категории
    document.getElementById('categoryForm').addEventListener('submit', async e => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        const response = await fetch('/dashboard/add_category', {
            method: 'POST',
            headers: { 'Content-Type':'application/json','Authorization': `Bearer ${token}` },
            body: JSON.stringify(data)
        });

        if(response.ok) {
            e.target.reset();
            loadDashboard();
        } else {
            alert('Ошибка при добавлении категории');
        }
    });

    loadDashboard();
});



