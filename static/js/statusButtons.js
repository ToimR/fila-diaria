/**
 * Gerencia apenas os destaques visuais da tabela principal.
 */
document.addEventListener('DOMContentLoaded', () => {
    
    document.querySelectorAll('.btn-chegou').forEach(btn => {
        btn.addEventListener('click', () => {
            const tr = btn.closest('tr');
            if (tr) tr.classList.add('highlight-yellow');
        });
    });

    document.querySelectorAll('.btn-desmarcar').forEach(btn => {
        btn.addEventListener('click', () => {
            const tr = btn.closest('tr');
            if (tr) tr.classList.remove('highlight-yellow');
        });
    });

    // Escuta o evento global disparado pelo lista_resumida.js
    document.addEventListener('limparCoresTabela', () => {
        document.querySelectorAll('tr.highlight-yellow').forEach(tr => {
            tr.classList.remove('highlight-yellow');
        });
    });
});