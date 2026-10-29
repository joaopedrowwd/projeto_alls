(function () {
  const drawer = document.getElementById('carrinho-drawer');
  const overlay = document.getElementById('carrinho-overlay');
  const conteudo = document.getElementById('carrinho-conteudo');
  const contador = document.getElementById('carrinho-contador');
  const toasts = document.getElementById('toasts');

  const CORES_TOAST = {
    success: 'bg-green-600 text-white',
    error: 'bg-red-600 text-white',
    warning: 'bg-yellow-500 text-black',
    info: 'bg-gray-800 text-white',
  };

  // Aviso temporário no canto da tela (será reaproveitado no dia 8)
  window.toast = function (mensagem, tipo = 'info') {
    const el = document.createElement('div');
    el.className = 'px-4 py-3 rounded shadow-lg text-sm max-w-xs ' + (CORES_TOAST[tipo] || CORES_TOAST.info);
    el.textContent = mensagem;
    toasts.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  };

  function abrir() {
    drawer.classList.remove('translate-x-full');
    overlay.classList.remove('hidden');
  }

  function fechar() {
    drawer.classList.add('translate-x-full');
    overlay.classList.add('hidden');
  }

  let timerContador = null;

  // Atualiza o selo: se aumentou, o número sobe de um em um
  function atualizarContador(novo) {
    const atual = parseInt(contador.textContent, 10) || 0;
    clearInterval(timerContador);

    if (novo <= atual) {                      // diminuiu ou igual: troca direto
      contador.textContent = novo;
      contador.classList.toggle('hidden', novo === 0);
      return;
    }

    contador.classList.remove('hidden');
    const passos = novo - atual;
    const intervalo = Math.min(120, 700 / passos);   // contagem leva no máximo ~0,7 s
    let valor = atual;

    timerContador = setInterval(() => {
      valor += 1;
      contador.textContent = valor;
      contador.animate(
        [{ transform: 'scale(1)' }, { transform: 'scale(1.6)' }, { transform: 'scale(1)' }],
        { duration: 220 }
      );
      if (valor >= novo) clearInterval(timerContador);
    }, intervalo);

    // pulinho no emoji do carrinho
    document.getElementById('carrinho-abrir').animate(
      [{ transform: 'rotate(0)' }, { transform: 'rotate(-18deg)' }, { transform: 'rotate(14deg)' }, { transform: 'rotate(0)' }],
      { duration: 400 }
    );
  }

  async function enviar(url, campos) {
    try {
      const resp = await fetch(url, { method: 'POST', body: new URLSearchParams(campos) });
      const dados = await resp.json();
      conteudo.innerHTML = dados.html;
      atualizarContador(dados.contador);
      if (dados.mensagem) window.toast(dados.mensagem, dados.tipo);
      return dados;
    } catch (e) {
      window.toast('Não foi possível atualizar o carrinho.', 'error');
      return null;
    }
  }

  document.getElementById('carrinho-abrir').addEventListener('click', abrir);
  document.getElementById('carrinho-fechar').addEventListener('click', fechar);
  overlay.addEventListener('click', fechar);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fechar(); });

  // Botões de dentro do carrinho (+, −, remover)
  conteudo.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-acao]');
    if (!btn || btn.disabled) return;
    const vid = btn.dataset.variante;
    if (btn.dataset.acao === 'remover') {
      enviar(drawer.dataset.urlRemover, { variante_id: vid });
    } else {
      enviar(drawer.dataset.urlAlterar, { variante_id: vid, pacotes: btn.dataset.pacotes });
    }
  });

  // Usado pela página do produto
  window.CarrinhoAPI = {
    abrir,
    adicionar: (variante_id, pacotes) =>
      enviar(drawer.dataset.urlAdicionar, { variante_id, pacotes }),
  };
})();