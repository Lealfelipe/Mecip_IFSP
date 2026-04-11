document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('statusChart');
    
    if (ctx) {
        const statusLabelsElement = document.getElementById('status-labels');
        const statusDataElement = document.getElementById('status-data');
        
        const statusLabels = statusLabelsElement ? JSON.parse(statusLabelsElement.textContent) : [];
        const statusData = statusDataElement ? JSON.parse(statusDataElement.textContent) : [];
        
        // Mapeamento de cores para cada status
        const statusColors = {
            'Aprovado': { bg: 'rgba(40, 167, 69, 0.2)', border: 'rgba(40, 167, 69, 1)' },
            'Reprovado': { bg: 'rgba(220, 53, 69, 0.2)', border: 'rgba(220, 53, 69, 1)' },
            'Em andamento': { bg: 'rgba(0, 123, 255, 0.2)', border: 'rgba(0, 123, 255, 1)' },
            'Pendente': { bg: 'rgba(255, 193, 7, 0.13)', border: 'rgba(255, 193, 7, 1)' },
            'Pendente ajuste': { bg: 'rgba(108, 117, 125, 0.2)', border: 'rgba(108, 117, 125, 1)' },
            'Pendente avaliação': { bg: 'rgba(255, 140, 0, 0.33)', border: 'rgba(255, 140, 0, 1)' },
            'Bloqueado': { bg: 'rgba(111, 66, 193, 0.2)', border: 'rgba(111, 66, 193, 1)' }
        };
        
        // Gerar cores baseadas nos labels
        const backgroundColor = statusLabels.map(label => statusColors[label]?.bg || 'rgba(200, 200, 200, 0.2)');
        const borderColor = statusLabels.map(label => statusColors[label]?.border || 'rgba(200, 200, 200, 1)');
        
        if (statusLabels.length > 0 && statusData.length > 0) {
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: statusLabels,
                    datasets: [{
                        label: 'Relatórios por Status',
                        data: statusData,
                        backgroundColor: backgroundColor,
                        borderColor: borderColor,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Distribuição de Relatórios por Status'
                        }
                    }
                }
            });
        }
    }
});
