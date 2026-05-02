// Array global para armazenar quem chegou
let listaPresentes = [];

/**
 * Função disparada pelo onload do HTML para reconstruir a lista 
 * baseada nos dados salvos no Banco de Dados (checkboxed marcados)
 * Modificação: Força a limpeza do array e garante captura precisa da hora.
 */
function carregarListaInicial() {
    // Limpa a lista na memória antes de ler do HTML para garantir sincronia total
    listaPresentes = []; 
    
    // Busca todos os checkboxes que vieram marcados (checked) do servidor
    const checks = document.querySelectorAll('.chk-status:checked');
    
    checks.forEach(chk => {
        // Localiza a linha (tr) correspondente para extrair Nome e Hora
        const linha = chk.closest('tr');
        const nome = linha.querySelector('.nome-coluna').innerText;
        
        // Tenta pegar a hora do input (se for montador) ou do texto da primeira célula (se for visualização)
        const entradaInput = linha.querySelector('.input-hora');
        const hora = entradaInput ? entradaInput.value : linha.cells[0].innerText.trim();
        const id = chk.value;

        // Adiciona ao array global garantindo que o ID seja a chave de unicidade
        if (!listaPresentes.some(item => item.id === id)) {
            listaPresentes.push({ nome: nome, hora: hora, id: id });
        }
    });
    
    // Atualiza a interface visual
    renderizarLista();
}

/**
 * Adiciona um piloto à lista de presentes
 */
function marcarChegada(nome, hora, id) {
    // Verifica se o piloto já está na lista para evitar duplicidade usando o ID
    const jaExiste = listaPresentes.some(item => item.id === id);
    
    if (!jaExiste) {
        // Se a hora vier de um input no momento do clique, pegamos o valor atualizado
        const linha = document.getElementById('chk-' + id).closest('tr');
        const entradaInput = linha.querySelector('.input-hora');
        const horaAtual = entradaInput ? entradaInput.value : hora;

        listaPresentes.push({ nome: nome, hora: horaAtual, id: id });
        
        // Marca o checkbox invisível para que o Python saiba que deve salvar como 1
        const checkbox = document.getElementById('chk-' + id);
        if (checkbox) checkbox.checked = true;

        renderizarLista();
    }
}

/**
 * Remove um piloto da lista de presentes
 */
function desmarcarChegada(nome, id) {
    // Filtra o array removendo o item pelo ID
    listaPresentes = listaPresentes.filter(item => item.id !== id);
    
    // Desmarca o checkbox invisível para que o Python saiba que deve salvar como 0
    const checkbox = document.getElementById('chk-' + id);
    if (checkbox) checkbox.checked = false;

    renderizarLista();
}

/**
 * Atualiza o HTML da lista flutuante
 */
function renderizarLista() {
    const ul = document.getElementById('lista-nomes-chegaram');
    const contador = document.getElementById('count-presentes');
    
    // Limpa a lista visual atual
    ul.innerHTML = '';
    
    // Ordena por horário para manter a organização na lista suspensa
    listaPresentes.sort((a, b) => a.hora.localeCompare(b.hora));

    // Cria os itens da lista dinamicamente
    listaPresentes.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${item.hora}</strong> - ${item.nome}`;
        ul.appendChild(li);
    });

    // Atualiza o número no contador do cabeçalho da lista
    contador.innerText = listaPresentes.length;
}
