(() => {
  const sinoBadge = document.getElementById('admin-sino-contador');
  const toastContainer = document.getElementById('admin-toast-container');
  if (!sinoBadge) return;

  const CHAVE_VISTOS = 'admin_pedidos_vistos_v1';
  let vistos = new Set(JSON.parse(sessionStorage.getItem(CHAVE_VISTOS) || '[]'));
  let primeiraCarga = vistos.size === 0;

  const brl = (centavos) =>
    (centavos / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  function mostrarToast(pedido) {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className =
      'bg-gray-900 text-white shadow-lg rounded-lg p-4 w-80 border border-gray-700 flex items-start justify-between gap-3 transition-all';
    toast.innerHTML = `
      <div>
        <p class="text-xs font-bold uppercase tracking-wider text-green-400">Novo pedido recebido!</p>
        <p class="font-semibold text-sm mt-0.5">Pedido ${pedido.codigo} · ${brl(pedido.total_centavos)}</p>
        <p class="text-xs text-gray-300">${pedido.cliente} (${pedido.criado_em})</p>
        <a href="/admin/pedidos?status=nao_lidos" class="inline-block mt-2 text-xs underline text-white hover:text-gray-200">
          Ver pedido →
        </a>
      </div>
      <button type="button" aria-label="Fechar" class="text-gray-400 hover:text-white text-lg leading-none">&times;</button>
    `;
    toast.querySelector('button').addEventListener('click', () => toast.remove());
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 8000);
  }

  async function checarNotificacoes() {
    try {
      const resp = await fetch('/admin/notificacoes', { headers: { 'Accept': 'application/json' } });
      if (!resp.ok) return;
      const dados = await resp.json();

      if (dados.contador > 0) {
        sinoBadge.textContent = dados.contador;
        sinoBadge.classList.remove('hidden');
      } else {
        sinoBadge.textContent = '0';
        sinoBadge.classList.add('hidden');
      }

      for (const p of dados.pedidos) {
        if (!vistos.has(p.id)) {
          vistos.add(p.id);
          // Mostra o toast tanto para pedidos novos quanto na primeira abertura se houver não lidos
          if (!primeiraCarga || dados.contador > 0) {
            mostrarToast(p);
          }
        }
      }
      primeiraCarga = false;
      sessionStorage.setItem(CHAVE_VISTOS, JSON.stringify([...vistos]));
    } catch (e) {
      // Silencia erros temporários de rede
    }
  }

  checarNotificacoes();
  setInterval(checarNotificacoes, 5000);
})();