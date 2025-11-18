const apiBase = '/api/products';

async function fetchProducts(){
  const res = await fetch(apiBase);
  const data = await res.json();
  return data;
}

function formatPriceBR(value){
  return value.toFixed(2).replace('.',',');
}

function parsePriceInput(input){
  const normalized = input.replace(/\s+/g,'').replace(',', '.');
  const n = Number(normalized);
  if (Number.isNaN(n)) return null;
  return n;
}

function renderProducts(list){
  const tbody = document.querySelector('#products-table tbody');
  tbody.innerHTML = '';
  list.forEach(p => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.name}</td>
      <td>${p.quantity}</td>
      <td>R$ ${formatPriceBR(Number(p.price))}</td>
      <td>
        <button class="btn-edit" data-id="${p.id}">Editar</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadAndRender(){
  try{
    const products = await fetchProducts();
    renderProducts(products);
  }catch(e){
    console.error('Erro ao carregar produtos', e);
  }
}

const form = document.getElementById('product-form');
const cancelBtn = document.getElementById('cancel-btn');

form.addEventListener('submit', async (ev)=>{
  ev.preventDefault();
  const id = document.getElementById('product-id').value;
  const name = document.getElementById('name').value.trim();
  const quantity = Number(document.getElementById('quantity').value);
  const priceRaw = document.getElementById('price').value.trim();

  const price = parsePriceInput(priceRaw);
  if (price === null){
    alert('Preço inválido. Use formato 199,99');
    return;
  }

  const payload = {name, quantity, price};

  try{
    if (id){
      const res = await fetch(apiBase + '/' + id, {
        method: 'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Falha ao editar');
    }else{
      const res = await fetch(apiBase, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      if (!res.ok) throw new Error('Falha ao criar');
    }
    form.reset();
    document.getElementById('product-id').value = '';
    loadAndRender();
  }catch(e){
    console.error(e);
    alert('Erro ao salvar produto');
  }
});

cancelBtn.addEventListener('click', ()=>{form.reset();document.getElementById('product-id').value='';});

document.querySelector('#products-table tbody').addEventListener('click', async (ev)=>{
  if (ev.target.matches('.btn-edit')){
    const id = ev.target.dataset.id;
    try{
      const res = await fetch(apiBase + '/' + id);
      if (!res.ok) throw new Error('Produto não encontrado');
      const p = await res.json();
      document.getElementById('product-id').value = p.id;
      document.getElementById('name').value = p.name;
      document.getElementById('quantity').value = p.quantity;
      document.getElementById('price').value = String(p.price).replace('.',',');
      window.scrollTo({top:0,behavior:'smooth'});
    }catch(e){console.error(e);alert('Erro ao buscar produto');}
  }
});

loadAndRender();
