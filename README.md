# retendoc# RegDoc — Monitor de Regularidade Docente

**Aplicativo:** https://retendoc.streamlit.app

O RegDoc transforma os dados públicos do Censo Escolar (Inep/MEC) em informação
gerencial sobre a **permanência de professores** nas redes públicas de ensino do
Brasil. Cobre **5.570 municípios** (série 2013–2025) e **mais de 209 mil escolas**
(série 2019–2025), sem custo, cadastro ou instalação.

## O que o aplicativo faz

| Módulo | Pergunta que responde |
|---|---|
| Painel da Rede | Como os estados se comparam e como a regularidade evoluiu? |
| Município | Qual é a situação do meu município? |
| Ranking de Atenção | Quem precisa de atenção prioritária agora? |
| Escola | Qual é a situação desta unidade e o que fazer? |
| Comparação | Como me posiciono frente aos pares? |
| Metodologia | Como cada número, cor e recomendação é calculado? |

Indicadores utilizados: **IRD** (regularidade docente, indicador central), **ATU**,
**AFD**, **IED** e **ICG**. Todas as regras de classificação (semáforo relativo à
média nacional, tendência por regressão em janela de 5 anos, alerta de ruptura e
prescrição por 12 perfis de escola) estão documentadas na página **Metodologia**
do próprio aplicativo.

## Estrutura do repositório

```
app.py                        # página inicial
pages/                        # módulos do aplicativo
utils/dados.py                # carga de dados e funções de classificação compartilhadas
municipal_consolidado.parquet # base municipal (2013–2025)
escola_consolidado.parquet    # base escolar (2019–2025)
requirements.txt
```

## Como atualizar os dados (ciclo anual do Censo)

1. Baixar os Indicadores Educacionais mais recentes no portal do Inep;
2. Executar a consolidação (padronização de códigos e cabeçalhos) gerando os
   arquivos `municipal_consolidado.parquet` e `escola_consolidado.parquet`;
3. Substituir os arquivos Parquet neste repositório;
4. Atualizar a constante `VERSAO_APP` em `utils/dados.py`.

O deploy no Streamlit Cloud é automático a partir do branch `main`.

## Stack

Python · Streamlit · Pandas · Plotly · PyArrow (ver `requirements.txt`).

## Contexto acadêmico e citação

Artefato desenvolvido no âmbito de pesquisa de doutorado (FUCAPE Business School)
sobre regularidade docente em redes públicas. Para citar:

> RegDoc: monitor de regularidade docente (versão 1.1). Dados: Inep/MEC,
> Indicadores Educacionais do Censo Escolar. Disponível em:
> https://retendoc.streamlit.app. Acesso em: [data].

## Limitações

O RegDoc sinaliza onde o problema de rotatividade pode estar; não mede qualidade
do ensino nem captura causas subjetivas. Detalhes na página Metodologia.
