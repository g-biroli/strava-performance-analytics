# 🏃‍♂️ Strava Performance Analytics

> **Pipeline completo de ELT + Dashboard interativo + Relatórios automatizados para análise de performance de corrida e ciclismo**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Sobre o Projeto

Sistema completo de **Ciência de Dados** e **Engenharia de Dados** que extrai, processa e visualiza dados de atividades físicas do **Strava API**. O projeto utiliza uma arquitetura ELT moderna para gerar insights sobre performance atlética, incluindo análise de pace, zonas de frequência cardíaca, mapas GPS de rotas e predições com Machine Learning.

### 🎯 Funcionalidades Principais

- **Pipeline ELT automatizado** — Extração completa de atividades históricas via paginação
- **Banco de dados relacional** — SQLite3 com 5 tabelas normalizadas e relacionadas
- **Dashboard interativo** — Streamlit com filtros temporais, gráficos dinâmicos e KPIs
- **Mapas de GPS** — Visualização de rotas com Folium e análise geoespacial
- **Análise avançada** — Pace por distância (5K, 10K, 21K), zonas de FC, volume de treino
- **Relatórios automatizados** — PDF quinzenal enviado por e-mail com resumo de performance
- **Machine Learning** — Predições de tempo futuro baseadas em dados históricos *(em desenvolvimento)*

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐
│   Strava API    │  ← OAuth 2.0 Authentication
└────────┬────────┘
         │ HTTP GET
         ↓
┌─────────────────┐
│  extract_load   │  ← Pipeline ELT com paginação
│     (Python)    │     • activities (tabela principal)
└────────┬────────┘     • activity_laps (splits km a km)
         │              • activity_zones (tempo em zonas FC/potência)
         ↓              • activity_streams (GPS ponto a ponto)
┌─────────────────┐     • athlete (perfil do atleta)
│   SQLite3 DB    │
│   (strava.db)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  transform.py   │  ← Transformações com Pandas
│   + Pandas      │     • Cálculo de pace (min/km)
└────────┬────────┘     • Agregações temporais (semanal, mensal)
         │              • Feature engineering para ML
         ↓
┌─────────────────┐
│   Streamlit     │  ← Dashboard Web Interativo
│   Dashboard     │     • Gráficos: Plotly + Folium
└─────────────────┘     • Filtros de data / tipo de atividade
         │              • Visualização de mapas GPS
         ↓
┌─────────────────┐
│  Relatório PDF  │  ← Automatização quinzenal
│  + E-mail       │     • ReportLab (geração PDF)
└─────────────────┘     • Schedule (cron quinzenal)
```

---

## 🗄️ Modelo de Dados

### Relacionamento das Tabelas

```sql
athlete (1) ──────< (N) activities
                           │
                           ├──────< (N) activity_laps
                           ├──────< (N) activity_zones
                           └──────< (N) activity_streams
```

### Schema Resumido

| Tabela | Descrição | Campos-chave |
|--------|-----------|--------------|
| **athlete** | Perfil do atleta | `id`, `firstname`, `weight`, `ftp` |
| **activities** | Atividades completas | `id`, `name`, `distance`, `moving_time`, `average_heartrate` |
| **activity_laps** | Splits por km | `activity_id`, `lap_index`, `average_speed`, `average_heartrate` |
| **activity_zones** | Tempo em zonas | `activity_id`, `zone_type`, `zone_index`, `time_in_zone` |
| **activity_streams** | Série temporal GPS | `activity_id`, `time_seconds`, `lat`, `lng`, `heartrate` |

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

- Python 3.9+
- Conta no [Strava Developers](https://developers.strava.com/)
- Aplicativo criado no painel de desenvolvedor Strava (OAuth 2.0)

### 1️⃣ Instalação

```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/strava-analytics.git
cd strava-analytics

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

### 2️⃣ Configuração das Credenciais

1. Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

2. Edite o arquivo `.env` e preencha suas credenciais:
```env
STRAVA_ACCESS_TOKEN=seu_access_token_aqui
STRAVA_CLIENT_ID=seu_client_id
STRAVA_CLIENT_SECRET=seu_client_secret
STRAVA_REFRESH_TOKEN=seu_refresh_token

EMAIL_DESTINATARIO=seu_email@gmail.com
EMAIL_REMETENTE=remetente@gmail.com
EMAIL_SENHA_APP=senha_de_app_gmail
```

⚠️ **IMPORTANTE:** O arquivo `.env` está no `.gitignore` e **nunca deve ser commitado**. Ele contém informações sensíveis.

### 3️⃣ Obter Credenciais do Strava

#### Passo a passo completo:

1. Acesse [Strava Developers](https://www.strava.com/settings/api)
2. Clique em **"Create New App"**
3. Preencha:
   - **Application Name:** Seu projeto
   - **Category:** Data Analysis
   - **Website:** http://localhost
   - **Authorization Callback Domain:** `localhost`
4. Após criar, copie o **Client ID** e **Client Secret**

#### Gerar Access Token:

```bash
# 1. Abra no navegador (substitua SEU_CLIENT_ID):
https://www.strava.com/oauth/authorize?client_id=SEU_CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all

# 2. Autorize e copie o 'code' da URL de retorno

# 3. Execute no terminal (substitua os valores):
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=SEU_CLIENT_ID \
  -d client_secret=SEU_CLIENT_SECRET \
  -d code=CODIGO_COPIADO_DA_URL \
  -d grant_type=authorization_code

# 4. Copie do JSON retornado:
#    - access_token
#    - refresh_token
```

### 4️⃣ Executar a Extração de Dados

```bash
# Executar o pipeline ELT (primeira carga histórica)
python extract_load.py
```

Isso vai:
- Criar o banco `strava.db` na pasta do projeto
- Extrair **todas** as suas atividades do Strava (com paginação automática)
- Carregar perfil do atleta, laps e zonas
- Gerar log em `extract_load.log`

**⏱️ Tempo estimado:** 2-5 minutos dependendo da quantidade de atividades

---

## 📊 Próximas Etapas (Roadmap)

- [x] **Etapa 1:** Pipeline ELT de extração e carga
- [ ] **Etapa 2:** Script de transformação com Pandas
- [ ] **Etapa 3:** Dashboard Streamlit com gráficos interativos
- [ ] **Etapa 4:** Visualização de mapas GPS
- [ ] **Etapa 5:** Geração de PDF e envio por e-mail
- [ ] **Etapa 6:** Automação quinzenal (Schedule / Cron)
- [ ] **Etapa 7:** Deploy em servidor (Streamlit Cloud / Railway)
- [ ] **Etapa 8:** Machine Learning para predição de performance

---

## 🛠️ Stack Tecnológica

| Categoria | Tecnologias |
|-----------|-------------|
| **Linguagem** | Python 3.9+ |
| **API** | Strava API v3 (REST, OAuth 2.0) |
| **Banco de Dados** | SQLite3 (local), PostgreSQL (futuro) |
| **Data Processing** | Pandas, NumPy |
| **Visualização** | Streamlit, Plotly, Folium |
| **Geração de PDF** | ReportLab |
| **Automação** | Schedule (Python), Cron |
| **Machine Learning** | Scikit-learn, XGBoost *(futuro)* |
| **Deploy** | Streamlit Cloud, Railway, Docker *(futuro)* |

---

## 📂 Estrutura de Arquivos

```
strava-analytics/
│
├── extract_load.py         # Pipeline ELT principal
├── transform.py            # Transformações e feature engineering (próxima etapa)
├── dashboard.py            # Dashboard Streamlit (próxima etapa)
├── generate_report.py      # Geração de relatório PDF (próxima etapa)
├── requirements.txt        # Dependências do projeto
├── .env.example            # Template de variáveis de ambiente
├── .gitignore              # Arquivos ignorados pelo Git
├── README.md               # Este arquivo
│
├── strava.db               # Banco de dados SQLite (gerado automaticamente)
├── extract_load.log        # Log de execução (gerado automaticamente)
│
└── assets/                 # Imagens e recursos (futuro)
    └── screenshots/
```

---

## 🔐 Segurança e Boas Práticas

✅ **O que ESTÁ no repositório:**
- Código-fonte Python
- Documentação completa
- Template de configuração (`.env.example`)
- Requirements e dependências

❌ **O que NÃO ESTÁ no repositório (protegido pelo `.gitignore`):**
- Arquivo `.env` com credenciais
- Banco de dados `strava.db` com seus dados pessoais
- Relatórios PDF gerados
- Logs de execução

---

## 📈 Exemplos de Análises Geradas

### KPIs Monitorados

- **Volume de Treino:** Distância total, tempo total, número de atividades
- **Performance:** Pace médio (min/km), velocidade média, evolução temporal
- **Fisiológico:** FC média/máxima, tempo por zona de FC, calorias
- **Geoespacial:** Mapa de calor de rotas, elevação acumulada, locais mais frequentes

### Métricas Calculadas

- Pace por distância (5K, 10K, 21K, maratona)
- Volume semanal/mensal agregado
- Progressão de performance ao longo do tempo
- Análise de consistência de treino
- Correlação entre variáveis (ex: FC x Pace)

---

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commitar suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Fazer push para a branch (`git push origin feature/nova-feature`)
5. Abrir um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

**Gabriel Biroli**

- LinkedIn: [linkedin.com/in/gabriel-biroli](https://www.linkedin.com/in/gabriel-biroli)
- Email: gabrielbiroli@gmail.com
- GitHub: [@g-biroli](https://github.com/g-biroli)

---

## 🙏 Agradecimentos

- [Strava API](https://developers.strava.com/) pela documentação completa
- Comunidade Python pela excelência das bibliotecas open-source
- Todos os contribuidores e apoiadores deste projeto

---

## 📚 Recursos Úteis

- [Documentação Strava API](https://developers.strava.com/docs/reference/)
- [Strava API Playground](https://developers.strava.com/playground)
- [Guia de OAuth 2.0 do Strava](https://developers.strava.com/docs/authentication/)
- [Decodificador de Polyline Online](https://developers.google.com/maps/documentation/utilities/polylineutility)

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela no repositório!**

</div>
