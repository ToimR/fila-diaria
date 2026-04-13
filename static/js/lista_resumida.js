/**
 * lista_resumida.js
 * Responsabilidades:
 * 1. Gerenciar a inclusão/remoção de nomes na lista lateral.
 * 2. Controlar o botão "Limpar Tudo" e disparar o evento de limpeza de cores.
 * 3. Gerenciar o comportamento dinâmico e pautado do Post-it.
 */

document.addEventListener('DOMContentLoaded', () => {
    const listaLateral = document.getElementById('nomes-confirmados');
    const btnLimpar = document.getElementById('btn-limpar-tudo');
    const textareaNotas = document.getElementById('notas-trabalho');
    const MARCADOR = "• ";

    // --- LÓGICA DA LISTA DE NOMES ---

    const gerenciarBotaoLimpar = () => {
        if (listaLateral && btnLimpar) {
            btnLimpar.style.display = listaLateral.children.length > 0 ? 'block' : 'none';
        }
    };

    const gerarID = (nome) => {
        return "item-" + btoa(unescape(encodeURIComponent(nome))).replace(/[^a-zA-Z0-9]/g, "");
    };

    document.querySelectorAll('.btn-chegou').forEach(btn => {
        btn.addEventListener('click', () => {
            const tr = btn.closest('tr');
            const nome = tr?.querySelector('.nome-txt')?.innerText;

            if (nome) {
                const idUnico = gerarID(nome);
                if (!document.getElementById(idUnico)) {
                    const li = document.createElement('li');
                    li.id = idUnico;
                    li.className = 'item-confirmado';
                    li.innerHTML = `<span>✔</span> ${nome}`;
                    listaLateral?.appendChild(li);
                    
                    if (typeof atualizarContador === "function") {
                        atualizarContador(1);
                    }
                    gerenciarBotaoLimpar();
                }
            }
        });
    });

    document.querySelectorAll('.btn-desmarcar').forEach(btn => {
        btn.addEventListener('click', () => {
            const tr = btn.closest('tr');
            const nome = tr?.querySelector('.nome-txt')?.innerText;

            if (nome) {
                const itemParaRemover = document.getElementById(gerarID(nome));
                if (itemParaRemover) {
                    itemParaRemover.remove();
                    if (typeof atualizarContador === "function") {
                        atualizarContador(-1);
                    }
                    gerenciarBotaoLimpar();
                }
            }
        });
    });

    btnLimpar?.addEventListener('click', () => {
        if (confirm("Deseja realmente limpar toda a lista de confirmados?")) {
            if (listaLateral) listaLateral.innerHTML = '';
            if (typeof resetarContador === "function") {
                resetarContador();
            }
            document.dispatchEvent(new CustomEvent('limparCoresTabela'));
            gerenciarBotaoLimpar();
        }
    });


    // --- LÓGICA DO POST-IT (OBSERVAÇÕES COM PAUTA E MARCADOR) ---

    if (textareaNotas) {
        
        // Inserir primeiro marcador se estiver vazio ao focar
        textareaNotas.addEventListener('focus', function() {
            if (this.value.trim() === "") {
                this.value = MARCADOR;
            }
        });

        textareaNotas.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault(); // Impede o comportamento padrão do Enter
                
                const start = this.selectionStart;
                const end = this.selectionEnd;
                const valorAtual = this.value;

                // Insere quebra de linha + marcador na posição do cursor
                this.value = valorAtual.substring(0, start) + "\n" + MARCADOR + valorAtual.substring(end);

                // Posiciona o cursor após o novo marcador (3 caracteres: \n e • e espaço)
                this.selectionStart = this.selectionEnd = start + 3;
                
                // Dispara o evento de input para ajustar a altura
                this.dispatchEvent(new Event('input'));
            }
        });

        textareaNotas.addEventListener('input', function() {
            // Ajuste automático de altura (sua lógica original mantida)
            this.style.height = 'auto';
            const alturaMaxima = window.innerHeight * 0.7;
            const novaAltura = Math.min(this.scrollHeight, alturaMaxima);
            
            this.style.height = novaAltura + 'px';

            if (this.scrollHeight > alturaMaxima) {
                this.style.overflowY = 'auto';
            } else {
                this.style.overflowY = 'hidden';
            }
        });
    }
});