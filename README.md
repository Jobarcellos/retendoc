[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21343128.svg)](https://doi.org/10.5281/zenodo.21343128)

# RegDoc — Monitor de Regularidade Docente

**Aplicativo:** https://retendoc.streamlit.app
...
# RegDoc — Monitor de Regularidade Docente

**Aplicativo:** https://retendoc.streamlit.app

O RegDoc transforma os dados públicos do Censo Escolar (Inep/MEC) em informação
gerencial sobre a **permanência de professores** nas redes públicas de ensino do
Brasil. Série histórica **2013–2025** (treze anos), cobrindo **5.570 municípios**
e **mais de 209 mil escolas ao longo da série** (cerca de 165 mil por ano; a
diferença corresponde a unidades abertas, fechadas ou recodificadas no período).
Sem custo, cadastro ou instalação.

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
média nacional, faixas absolutas oficiais do Inep, tendência por regressão em
janela de 5 anos, alerta de ruptura e prescrição por 12 perfis de escola) estão
documentadas na página **Metodologia** do próprio aplicativo.

## Estrutura do repositório

```
app.py                        # página inicial
pages/                        # módulos do aplicativo
utils/dados.py                # carga de dados e funções de classificação compartilhadas
municipal_consolidado.parquet # base municipal (2013–2025)
escola_consolidado.parquet    # base escolar (2013–2025)
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

## Licença

Código-fonte sob licença **MIT** (ver `LICENSE`). Os arquivos Parquet derivam dos
Indicadores Educacionais do Censo Escolar, dados abertos publicados pelo Inep/MEC.
Nenhum dado pessoal ou identificável foi coletado, processado ou distribuído.

## Contexto acadêmico e citação

Artefato desenvolvido no âmbito de pesquisa de doutorado (FUCAPE Business School)
sobre regularidade docente em redes públicas de ensino.

Cada versão publicada deste repositório é arquivada no Zenodo com DOI próprio.
Para citar, use o DOI da versão utilizada (ver badge no topo desta página) ou a
referência abaixo:

> SANTANNA, Joelma Barcellos. **RegDoc: monitor de regularidade docente em redes
> públicas de ensino** (versão 1.2.0). Software. Vitória: FUCAPE Business School,
> 2026. Dados: Inep/MEC, Indicadores Educacionais do Censo Escolar.
> Disponível em: https://retendoc.streamlit.app

O arquivo `CITATION.cff` na raiz do repositório fornece os metadados de citação em
formato legível por máquina.

## Limitações

O RegDoc sinaliza **onde a permanência docente está fragilizada** — não mede
rotatividade diretamente, não afere qualidade do ensino e não captura causas
subjetivas da saída de professores.

O IRD expressa o **padrão acumulado de vínculo do professor com a escola ao longo
de cinco anos**, e não uma taxa de entrada e saída no período. Regularidade e
rotatividade são conceitos distintos e não devem ser usados como sinônimos.

Detalhes e fórmulas na página **Metodologia** do aplicativo.
