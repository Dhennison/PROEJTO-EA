# Modelo D v2.09 — cobertura e recuperação

[ZIP somente Experts](../ModeloD_Integrado_Sem_Transporte_v2_09.zip) · [Instruções completas](LEIA_PRIMEIRO_v2_09.txt) · [Arquivos alterados](ARQUIVOS_ALTERADOS.txt) · [SHA-256](SHA256SUMS.txt)

A v2.09 corrige a dependência da cobertura geral dos SL/TP do primeiro nível. Registra a causa específica da cobertura e evidências comparáveis de ticks/M1. Depois dos dez minutos de retry rápido, continua sondagens a cada dois minutos com entradas bloqueadas até recompor a lacuna. Não elimina a necessidade de dados válidos e não afirma ter corrigido a causa interna do histórico da corretora.

Testes novos: [47/0 com sanitizadores](VALIDACAO_FOCUSED_v2_09.txt). [Regressão existente](VALIDACAO_COMPLETA_v2_09_SANITIZERS.txt): 631/0, 104/0, falhas 10/0, runtime 29/0, repetição, retomada e inicialização. São APIs simuladas, não compilação MQL5. O Script e o formato do diário não foram alterados.

## Próxima ação

Substituir somente Experts, preservar Common/Files, compilar o EA no MetaEditor e observar primeiro com a rede ligada. WIN$N M5, parâmetros padrão, negociação algorítmica desativada. Enviar compilação, TXT completo e Experts; Wi-Fi continua adiado até a análise dessa versão. Não há EX5 produzido neste ambiente.

## Reproduzir testes novos

Em um ambiente com Python e g++ e com a base v2.07 extraída e Experts sobrepostos pela v2.09:

```sh
python run_focused_v209.py --root /caminho/ModeloD_Integrado_Sem_Transporte --sanitize
```

Para regressão existente, a partir dessa raiz:

```sh
python tests/run_local.py --sanitize --report /tmp/VALIDACAO_COMPLETA_v2_09.txt
```

O runner novo lê o harness existente e adapta somente sintaxe de arrays, input/properties e APIs simuladas em uma pasta temporária; não altera fontes do projeto. Em ambientes com ptrace restrito, LeakSanitizer pode precisar de execução fora dessa restrição. Falha de runner não equivale a teste aprovado.
