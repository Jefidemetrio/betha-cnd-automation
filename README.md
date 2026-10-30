# Betha Cidadão Web - Automação de Certidão Negativa de Imóvel (CND)

## 📋 Visão Geral

Este repositório contém uma solução completa e reutilizável para automação da emissão e download de **Certidão Negativa de Imóvel (CND)** no sistema **Betha Cidadão Web** (município de Balneário Gaivota/SC).

O script automatiza todo o fluxo: seleção de estado/município, autenticação por CPF, consulta de imóveis, e download dos PDFs das certidões via Playwright.

---

## 🎯 Objetivo

Automatizar a emissão e download de PDFs de CND de imóveis no portal Betha Cidadão Web, garantindo:
- Fluxo completo de navegação (estado → município → entidade → CPF → consulta)
- Captura dos PDFs gerados sob demanda
- Validação de integridade dos arquivos (assinatura `%PDF-`, tamanho, SHA-256)
- Código reutilizável e sem dependências externas desnecessárias

---

## 🏗️ Arquitetura do Sistema Alvo

### Sistema: Betha Cidadão Web 3
- **URL Base**: `https://e-gov.betha.com.br/cdweb/03114-578/`
- **Tecnologias**: JSF + RichFaces/AJAX + PDF.js viewer
- **Autenticação**: CPF (sem senha, apenas consulta pública)

### Fluxo de Navegação

| Etapa | URL/Componente | Ação |
|-------|----------------|------|
| 1 | `/main.faces` | Seleção de estado (SC = 22) |
| 2 | AJAX | Carrega municípios do estado |
| 3 | Select | Seleciona município (Balneário Gaivota = 1606) |
| 4 | Link "Acessar" | `a#mainForm:selecionar` → `/contribuinte/main.faces` |
| 5 | Menu | Clica "Certidão negativa de imóvel" → `/contribuinte/rel_cndimovel.faces` |
| 6 | Formulário | Preenche CPF em `input[name="mainForm:cpf"]` |
| 7 | Botão Continuar | `input[id="mainForm:btCpf"]` (requer `force=True` no Playwright) |
| 8 | Tabela | Lista imóveis com ícone de impressora na coluna "Emitir" |

---

## 🔧 Mecanismo de Emissão do PDF

### JavaScript Nativo (`setIRefer`)
```javascript
// Em sys.js
function setIRefer(value) {
    $j('#iReferList').val(value);  // Define property_id no hidden field
    processing();                   // Chama processamento AJAX
}
```

### Processamento (`bfc.js`)
```javascript
function processing() {
    // Submete formulário via AJAX para /processrep.faces
    // Gera PDF sob demanda
    // Retorna URL do PDF.js viewer: /processrep.faces
}
```

### Entrega do PDF
1. `setIRefer(property_id)` → define `#iReferList` + chama `processing()`
2. Servidor gera PDF em `/reportasync.faces/anonymous_cnd-imovel-padrao_{timestamp}.pdf`
3. Iframe carrega PDF.js viewer: `/processrep.faces`
3. Viewer carrega PDF via parâmetro `file=/reportasync.faces/anonymous_cnd-imovel-padrao_{ts}.pdf`
4. **PDF real disponível em**: `https://e-gov.betha.com.br/cdweb/03114-578/contribuinte/reportasync.faces/anonymous_cnd-imovel-padrao_{timestamp}.pdf`

---

## 📋 Requisitos

### Dependências
```bash
pip install playwright
playwright install chromium
```

### Sistema
- Python 3.10+
- Chromium/Chrome (binário do Playwright: `/opt/data/playwright-browsers/chromium-1248/chrome-linux64/chrome`)
- Acesso à internet (portal Betha)

### Configuração de Ambiente
- Perfil persistente Playwright: `/tmp/betha_session`
- Diretório de download: `./downloads_pdf/`

---

## 📁 Estrutura do Repositório

```
betha_cnd_repo/
├── final_complete.py          # Script principal (5.6KB)
├── downloads_pdf/             # PDFs gerados (exemplos)
│   ├── CND_08146533914_prop24723.pdf
│   └── CND_08146533914_prop24851.pdf
├── README.md                  # Esta documentação
└── docs/
    └── fluxo_detalhado.md     # Documentação técnica detalhada
```

---

## 🚀 Como Executar

### 1. Preparação
```bash
cd betha_cnd_repo
mkdir -p downloads_pdf
```

### 2. Executar
```bash
python final_complete.py
```

### 3. Verificar Saída
```bash
ls -la downloads_pdf/
# Deve mostrar:
# CND_08146533914_prop24723.pdf (21KB)
# CND_08146533914_prop24851.pdf (21KB)
```

### 3. Validar Integridade
```bash
python3 -c "
import hashlib
for f in ['CND_08146533914_prop24723.pdf', 'CND_08146533914_prop24851.pdf']:
    with open(f, 'rb') as fh:
        data = fh.read()
        print(f'{f}: PDF={data[:5]==b\"%PDF-\"}, size={len(data)}, sha256={hashlib.sha256(data).hexdigest()}')"
```

---

## ⚙️ Configurações Principais (no script)

```python
# URLs
MAIN_URL = "https://e-gov.betha.com.br/cdweb/03114-578/main.faces"
CND_URL  = "https://e-gov.betha.com.br/cdweb/03114-578/contribuinte/rel_cndimovel.faces"

# Seletores
ESTADO_SELECT = "#mainForm\\:estados"
MUNICIPIO_SELECT = "#mainForm\\:municipios"
ACESSAR_LINK = "a#mainForm\\:selecionar"
CPF_INPUT = 'input[name="mainForm:cpf"]'
CONTINUAR_BTN = 'input[id="mainForm:btCpf"]'
EMITIR_TEXT = "text=Emitir"

# Valores fixos (Balneário Gaivota/SC)
ESTADO_SC = "22"
MUNICIPIO_GAIVOTA = "1606"
CPF_EXEMPLO = "08146533914"
PROPRIEDADES = [24723, 24851]  # IDs dos imóveis

# Playwright
CHROMIUM_PATH = "/opt/data/playwright-browsers/chromium-1248/chrome-linux64/chrome"
USER_DATA_DIR = "/tmp/betha_session"
```

---

## 🔍 Validação de Integridade dos PDFs

Cada PDF gerado é validado automaticamente:

| Check | Critério |
|-------|----------|
| **Assinatura** | `header == b'%PDF-'` |
| **Tamanho** | > 0 bytes (~21KB) |
| **Hash SHA-256** | Calculado e logado |

### Exemplo de Saída Esperada
```
=== Processing property 24723 ===
Invoked setIRefer(24723) via JavaScript
Found PDF URL in iframe: /cdweb/03114-578/contribuinte/reportasync.faces/anonymous_cnd-imovel-padrao_1793367999023.pdf
Full PDF URL: https://e-gov.betha.com.br/cdweb/03114-578/contribuinte/reportasync.faces/anonymous_cnd-imovel-padrao_1793367999023.pdf
PDF saved: /path/to/downloads_pdf/CND_08146533914_prop24723.pdf
Assinatura %PDF- válida: True
SHA-256: 49a1f916a86dbddab40a8b15a3aaafda3c4340fd863a4c14a33c19e4a2681532
```

---

## ⚠️ Pontos de Atenção (Gotchas)

| Problema | Solução |
|----------|---------|
| Botão "Continuar" sobreposto | Usar `force=True` no `page.click()` |
| Dropdown de municípios vazio | Aguardar `options.length > 1` após selecionar estado |
| CPF não aparece | Clicar em "Certidão negativa de imóvel" após acessar entidade |
| PDF não baixa via `expect_download` | Capturar URL do iframe e baixar via HTTP direto |
| Timeout em `wait_for_load_state` | Usar `domcontentloaded` em vez de `networkidle` |

---

## 🔄 Reutilização para Outros Municípios/Imóveis

Para adaptar a outro município:

```python
# Alterar apenas estes valores:
ESTADO_SIGLA = "XX"           # Código do estado (ex: 22 = SC)
MUNICIPIO_CODIGO = "XXXXX"    # Código do município no sistema
PROPRIEDADES = [id1, id2, ...] # IDs dos imóveis desejados
```

Os IDs dos imóveis podem ser obtidos inspecionando a tabela na coluna "Código" ou via `onclick="setIRefer(ID)"`.

---

## 📦 Entregáveis do Repositório

| Arquivo | Descrição |
|---------|-----------|
| `final_complete.py` | Script principal autônomo |
| `downloads_pdf/*.pdf` | Exemplos de PDFs válidos gerados |
| `README.md` | Esta documentação |
| `docs/fluxo_detalhado.md` | Documentação técnica expandida |

---

## 📝 Licença e Uso

- **Uso Interno**: Automação para consultas legítimas no portal Betha
- **Responsabilidade**: Respeitar Termos de Uso do portal Betha
- **Dados Sensíveis**: CPF usado apenas como exemplo; substituir por variável de ambiente em produção

---

## 📞 Suporte

Para dúvidas sobre implementação ou adaptação:
1. Verificar logs do Playwright (debug: `headless=False`)
2. Inspecionar `page.content()` em pontos de falha
3. Verificar network tab para requests falhando
4. Confirmar se IDs dos imóveis existem na tabela

---

*Documentação gerada em 2024-10-30 - Versão 1.0*
*Script testado com Playwright 1.62.0 + Chromium 124*
*Município: Balneário Gaivota/SC (código 1606)*