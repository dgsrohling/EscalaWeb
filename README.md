# 🏛️ EscalaWeb

Sistema de Gestão de Escalas de Sobreaviso para Prefeituras

## 📋 Sobre o Projeto

**EscalaWeb** é um sistema web desenvolvido em Flask para gerenciar escalas de sobreaviso de servidores municipais, com geração automática de planilhas formatadas e dashboard estatístico.

### Funcionalidades Principais

- ✅ **Gestão de Servidores e Secretarias**
- ✅ **Criação de Escalas de Sobreaviso** (3 grupos: GERAL, SAÚDE 17h, SAÚDE 17h30)
- ✅ **Distribuição Automática ou Manual** de escalas por dia
- ✅ **Registro de Plantões Realizados** com cálculo automático de horas
- ✅ **Geração de Planilhas Excel** formatadas e prontas para impressão
  - Escala mensal com 3 grupos
  - Calendário visual mensal
  - Relatório individual de horas extras
- ✅ **Dashboard com Estatísticas** (Top plantonistas, distribuição por grupo, etc.)
- ✅ **Sistema de Auditoria** completo
- ✅ **Exportação de Relatórios**

## 🚀 Tecnologias

- **Backend:** Python 3.10+ / Flask
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Frontend:** Bootstrap 5 + JavaScript
- **Geração Excel:** openpyxl
- **Autenticação:** Flask-Login
- **Gráficos:** Chart.js

## 📦 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/EscalaWeb.git
cd EscalaWeb
```

2. **Crie um ambiente virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Inicialize o banco de dados**
```bash
python app.py init-db
```

6. **Execute a aplicação**
```bash
python app.py
```

7. **Acesse no navegador**
```
http://localhost:5000
```

### Usuário Padrão

- **Login:** admin
- **Senha:** admin123

⚠️ **Importante:** Altere a senha padrão após o primeiro login!

## 📂 Estrutura do Projeto

```
escalaweb/
├── app.py                    # Entry point da aplicação
├── config.py                 # Configurações
├── requirements.txt          # Dependências Python
├── models/                   # Modelos do banco de dados
├── routes/                   # Rotas/Endpoints
├── services/                 # Lógica de negócio e geradores Excel
├── utils/                    # Utilitários e helpers
├── templates/                # Templates HTML
├── static/                   # CSS, JS e imagens
├── database/                 # Banco de dados SQLite
├── exports/                  # Planilhas geradas
└── logs/                     # Logs do sistema
```

## 🎯 Uso Rápido

### 1. Cadastrar Servidores
`Menu > Cadastros > Servidores`

### 2. Criar Escala
`Menu > Novo > Criar Escala`
- Selecione o tipo (GERAL ou SAÚDE)
- Escolha a competência (mês/ano)
- Distribua os servidores (manual ou automático)
- Gere a planilha Excel

### 3. Registrar Plantões
`Menu > Novo > Registrar Plantão`
- Selecione o servidor e competência
- Marque os dias trabalhados
- Gere o relatório individual

## 📊 Planilhas Geradas

O sistema gera 3 tipos de planilhas Excel:

1. **Escala de Sobreaviso (3 Grupos)** - Consolidado mensal com todos os grupos
2. **Calendário Visual** - Formato de calendário com nome dos plantonistas
3. **Relatório Individual** - Horas extras por servidor para RH/Pagamento

## 🔒 Segurança

- ✅ Autenticação obrigatória
- ✅ Senhas criptografadas (bcrypt)
- ✅ Proteção CSRF em formulários
- ✅ Sistema de auditoria completo
- ✅ Validação de dados no backend

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- **Desenvolvedor Principal** - D. Rohling

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através de dio_rohling@hotmail.com

---

⭐ Se este projeto foi útil para você, considere dar uma estrela!
