# 🎮 SteamMatch

Sistema de recomendação de jogos Steam com interface estilo Tinder no navegador, powered por TF-IDF e similaridade cosseno.

---

## Como funciona

O SteamMatch aprende seus gostos enquanto você faz swipe nos jogos. A cada like, o sistema ajusta as recomendações usando estratégias progressivas:

| Fase | Critério | Estratégia |
|------|----------|------------|
| Início | 0 interações | Jogo aleatório |
| Aquecimento | 1–2 interações | Jogos populares (IMDb score) |
| Personalizado | ≥ 3 likes | Similaridade de conteúdo (TF-IDF) |

A cada 5 likes aparece uma tela de **Match** com seus gêneros favoritos e as melhores recomendações do momento.

---

## Estrutura

```
steamatch/
├── main.py              # Launcher: sobe a API e abre o navegador
├── api.py               # Servidor Flask — endpoints REST + serve o frontend
├── dados/
│   └── games.csv        # Dataset FronkonGames (não incluído no git)
├── modelos/
│   ├── carregador.py    # Carregamento e preparação dos dados
│   ├── baseline.py      # Recomendação por popularidade
│   └── conteudo.py      # TF-IDF + similaridade cosseno on-demand
├── interface/
│   └── sessao.py        # Estratégia de recomendação e estado da sessão
└── frontend/
    ├── index.html
    ├── css/style.css
    └── js/
        ├── logica.js    # Sessão e chamadas à API
        └── interface.js # DOM, eventos e animações
```

---

## Instalação

**Requisitos:** Python 3.10+

```bash
pip install pandas numpy scikit-learn flask flask-cors rich
```

---

## Dataset

O projeto usa o dataset público do Kaggle:

- [Steam Games Dataset — FronkonGames](https://www.kaggle.com/datasets/fronkongames/steam-games-dataset) (~122k jogos com gêneros, tags, descrição e avaliações)

Após baixar, coloque o arquivo em:

```
steamatch/dados/games.csv
```

> O arquivo não está no repositório pois tem 371 MB (acima do limite do GitHub).

---

## Como rodar

```bash
cd steamatch
python main.py
```

O launcher:
1. Sobe o servidor Flask (`api.py`) em background
2. Aguarda a API carregar o modelo (~15–30 segundos)
3. Abre `http://localhost:5000` no navegador automaticamente

Para encerrar: `Ctrl+C` no terminal.

---

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/health` | Status do servidor e total de jogos |
| `GET` | `/api/jogos?q=nome&limit=20` | Busca jogos por nome |
| `POST` | `/api/proximo` | Próximo jogo para o swipe (replica lógica do backend) |
| `POST` | `/api/recomendar` | N recomendações por estratégia |

**Body de `/api/proximo`:**
```json
{ "curtidos": [], "rejeitados": [], "vistos": [] }
```

**Body de `/api/recomendar`:**
```json
{ "estrategia": "conteudo", "jogos": ["CS2"], "excluir": [], "n": 5 }
```

---

## Modelos

**Baseline (popularidade)**
Pontuação ponderada estilo IMDb que equilibra ratio de avaliações positivas com volume de reviews. Usado no início da sessão (< 3 likes).

**Conteúdo (TF-IDF)**
Vetoriza gêneros, tags e descrição de cada jogo. Gêneros têm peso duplo. Calcula similaridade via dot product on-demand (sem pré-computar a matriz n×n), combinando similaridade de conteúdo (60%) com popularidade (40%). Ativado a partir de 3 likes.
