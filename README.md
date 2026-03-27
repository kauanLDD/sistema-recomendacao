# 🎮 SteamMatch

Sistema de recomendação de jogos Steam com interface estilo Tinder — disponível no terminal (Python) e no navegador (HTML+CSS+JS).

---

## Como funciona

O SteamMatch aprende seus gostos enquanto você faz swipe nos jogos. A cada like, o sistema ajusta as recomendações usando duas estratégias progressivas:

| Fase | Critério | Estratégia |
|------|----------|------------|
| Início | < 3 likes | Jogos populares (baseline) |
| Personalizado | ≥ 3 likes | Similaridade de conteúdo (TF-IDF) |

A cada 5 likes aparece uma tela de **Match** com seus gêneros favoritos e as melhores recomendações do momento. Parte dos jogos exibidos são escolhas aleatórias para garantir diversidade.

---

## Estrutura

```
steamatch/
├── main.py                      # Ponto de entrada (terminal)
├── exportar_dados_frontend.py   # Gera dados.js a partir do games.csv
├── dados/
│   └── games.csv                # Dataset FronkonGames (não incluído no git)
├── modelos/
│   ├── carregador.py            # Carregamento e preparação dos dados
│   ├── baseline.py              # Recomendação por popularidade
│   └── conteudo.py              # TF-IDF + similaridade cosseno
├── interface/
│   ├── sessao.py                # Gerenciamento da sessão e estratégia
│   └── terminal.py              # Interface visual com Rich
└── frontend/
    ├── index.html               # Interface web (abre direto no navegador)
    ├── css/style.css
    └── js/
        ├── dados.js             # Jogos (mock ou exportados do dataset)
        ├── logica.js            # Lógica de recomendação simulada
        └── interface.js         # DOM, eventos e animações
```

---

## Instalação

**Requisitos:** Python 3.10+

```bash
pip install pandas numpy scikit-learn rich
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

## Uso

### Terminal

```bash
cd steamatch
python main.py
```

**Controles:**
- `L` — Like
- `D` — Dislike
- `Q` — Sair e ver resumo final

### Frontend web

Abra `steamatch/frontend/index.html` diretamente no navegador. Por padrão usa 20 jogos mockados.

**Para usar os dados reais do dataset:**

```bash
cd steamatch
python exportar_dados_frontend.py
```

Isso gera um novo `dados.js` com os 300 melhores jogos do `games.csv`. Depois é só abrir o `index.html` normalmente.

---

## Modelos

**Baseline (popularidade)**
Pontuação ponderada estilo IMDb que equilibra ratio de avaliações positivas com volume de reviews. Usado enquanto o sistema ainda não conhece seu gosto (< 3 likes).

**Conteúdo (TF-IDF)**
Vetoriza gêneros, tags e descrição de cada jogo com TF-IDF. Gêneros têm peso duplo. Calcula similaridade via dot product on-demand (sem pré-computar matriz n×n), combinando similaridade de conteúdo (60%) com popularidade (40%). Ativado a partir de 3 likes.
