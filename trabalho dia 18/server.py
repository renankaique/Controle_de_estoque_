#!/usr/bin/env python3
import json
import sqlite3
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import re

# Nome do arquivo do banco de dados SQLite
DB = 'estoque.db'

# Criação da tabela de produtos caso não exista
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- identificador único
    name TEXT NOT NULL,                   -- nome do produto
    quantity INTEGER NOT NULL DEFAULT 0,  -- quantidade em estoque
    price REAL NOT NULL DEFAULT 0.0       -- preço do produto
)
''')
conn.commit()
conn.close()

# Classe que define a API HTTP
class APIHandler(SimpleHTTPRequestHandler):
    # Função auxiliar para configurar cabeçalhos da resposta
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        # Permite requisições de qualquer origem (CORS)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # Responde às requisições OPTIONS (necessário para CORS)
    def do_OPTIONS(self):
        self._set_headers()

    # Método GET: lista todos os produtos ou retorna um produto específico
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        # Expressão regular para /api/products ou /api/products/<id>
        m = re.match(r'^/api/products(?:/([0-9]+))?$', path)
        if m:
            pid = m.group(1)  # id do produto, se existir na URL
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            if pid:
                # Busca produto pelo id
                c.execute('SELECT id, name, quantity, price FROM products WHERE id=?', (pid,))
                row = c.fetchone()
                conn.close()
                if not row:
                    # Produto não encontrado
                    self._set_headers(404)
                    self.wfile.write(json.dumps({'error': 'Not found'}).encode())
                    return
                # Monta objeto JSON do produto
                prod = {'id': row[0], 'name': row[1], 'quantity': row[2], 'price': row[3]}
                self._set_headers(200)
                self.wfile.write(json.dumps(prod).encode())
                return
            else:
                # Lista todos os produtos
                c.execute('SELECT id, name, quantity, price FROM products ORDER BY id DESC')
                rows = c.fetchall()
                conn.close()
                products = [{'id': r[0], 'name': r[1], 'quantity': r[2], 'price': r[3]} for r in rows]
                self._set_headers(200)
                self.wfile.write(json.dumps(products).encode())
                return
        # Se não bater com a rota, usa comportamento padrão
        return super().do_GET()

    # Método POST: adiciona um novo produto
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/products':
            # Lê corpo da requisição
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            try:
                # Valida dados recebidos
                name = data.get('name', '').strip()
                quantity = int(data.get('quantity', 0))
                price = data.get('price', 0)
                if isinstance(price, str):
                    price = float(price.replace(',', '.'))
                if not name:
                    raise ValueError('Nome vazio')
            except Exception as e:
                # Dados inválidos
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': str(e)}).encode())
                return
            # Insere no banco
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute('INSERT INTO products (name, quantity, price) VALUES (?,?,?)',
                      (name, quantity, price))
            conn.commit()
            new_id = c.lastrowid
            conn.close()
            # Retorna id do novo produto
            self._set_headers(201)
            self.wfile.write(json.dumps({'id': new_id}).encode())
            return
        self._set_headers(404)

    # Método PUT: atualiza um produto existente
    def do_PUT(self):
        parsed = urlparse(self.path)
        m = re.match(r'^/api/products/([0-9]+)$', parsed.path)
        if m:
            pid = m.group(1)
            # Lê corpo da requisição
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            try:
                # Valida dados recebidos
                name = data.get('name', '').strip()
                quantity = int(data.get('quantity', 0))
                price = data.get('price', 0)
                if isinstance(price, str):
                    price = float(price.replace(',', '.'))
                if not name:
                    raise ValueError('Nome vazio')
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': str(e)}).encode())
                return
            # Atualiza no banco
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute('UPDATE products SET name=?, quantity=?, price=? WHERE id=?',
                      (name, quantity, price, pid))
            conn.commit()
            updated = c.rowcount
            conn.close()
            if updated == 0:
                # Produto não encontrado
                self._set_headers(404)
                return
            # Sucesso
            self._set_headers(200)
            self.wfile.write(json.dumps({'ok': True}).encode())
            return
        self._set_headers(404)

    # Método DELETE: remove um produto pelo id
    def do_DELETE(self):
        parsed = urlparse(self.path)
        m = re.match(r'^/api/products/([0-9]+)$', parsed.path)
        if m:
            pid = m.group(1)
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute('DELETE FROM products WHERE id=?', (pid,))
            conn.commit()
            deleted = c.rowcount
            conn.close()

            if deleted == 0:
                # Produto não encontrado
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Produto não encontrado'}).encode())
                return

            # Sucesso
            self._set_headers(200)
            self.wfile.write(json.dumps({'ok': True}).encode())
            return

        self._set_headers(404)

# Inicializa o servidor HTTP na porta 8000
if __name__ == '__main__':
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    httpd.serve_forever()
