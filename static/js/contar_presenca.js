/**
 * Gerencia exclusivamente o cálculo numérico dos presentes.
 */
function atualizarContador(valor) {
    const spanContador = document.getElementById('contador');
    if (spanContador) {
        let totalAtual = parseInt(spanContador.innerText) || 0;
        let novoTotal = totalAtual + valor;
        spanContador.innerText = novoTotal < 0 ? 0 : novoTotal;
    }
}

function resetarContador() {
    const spanContador = document.getElementById('contador');
    if (spanContador) spanContador.innerText = '0';
}