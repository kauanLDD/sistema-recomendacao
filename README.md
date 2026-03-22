# 🎮 SteamMatch

Sistema de recomendação de jogos Steam com interface estilo Tinder no terminal.

---

## Como funciona

O SteamMatch aprende seus gostos enquanto você faz swipe nos jogos. A cada like, o sistema ajusta as recomendações usando três estratégias progressivas:

| Fase | Critério | Estratégia |
|------|----------|------------|
| Início | < 3 likes | Jogos populares (baseline) |
| Intermediário | 3–7 likes | Similaridade de conteúdo (TF-IDF) |
| Avançado | ≥ 8 interações e ≥ 3 likes | Híbrido (conteúdo + colaborativo + popularidade) |

A cada 5 likes aparece uma tela de **Match** com seus gêneros favoritos e as melhores recomendações do momento. 30% dos jogos exibidos são escolhas aleatórias para garantir diversidade.

---

## Estrutura

```
steamatch/
├── main.py                  # Ponto de entrada
├── dados/
│   ├── steam-200k.csv       # Interações de usuários (200k registros)
│   └── steam_games.csv      # Metadados dos jogos (~52k jogos)
├── modelos/
│   ├── carregador.py        # Carregamento, merge e popularidade
│   ├── baseline.py          # Recomendação por popularidade
│   ├── conteudo.py          # TF-IDF + similaridade cosseno
│   └── colaborativo.py      # Filtragem colaborativa item-item
└── interface/
    ├── sessao.py            # Gerenciamento da sessão e estratégia
    └── terminal.py          # Interface visual com Rich
```

---

## Instalação

**Requisitos:** Python 3.10+

```bash
pip install pandas numpy scikit-learn scipy rich
```

---

## Uso

```bash
cd steamatch
python main.py
```

**Controles:**
- `L` — Like 💚
- `D` — Dislike ❌
- `Q` — Sair e ver resumo final

---

## Dataset

O projeto usa dois datasets públicos do Kaggle:

- [Steam 200k](https://www.kaggle.com/datasets/tamber/steam-video-games) — comportamento de 200k usuários (compras e horas jogadas)
- [Steam Games](https://www.kaggle.com/datasets/nikdavis/steam-store-games) — metadados de ~52k jogos (gênero, tags, descrição)

---

## Modelos

**Baseline (popularidade)**
Pontuação ponderada estilo IMDb que equilibra média de horas com volume de jogadores.

**Conteúdo (TF-IDF)**
Vetoriza gêneros, tags e descrição de cada jogo. Gêneros têm peso duplo. Combina similaridade cosseno (60%) com popularidade (40%).

**Colaborativo (item-item)**
Matriz esparsa de horas jogadas por usuário. Similaridade cosseno entre jogos combinada com popularidade (60%/40%).

**Híbrido**
Combina os dois modelos com bônus de popularidade: `0.5 × conteúdo + 0.5 × colaborativo + 0.2 × popularidade`, renormalizado entre 0 e 1.
