# Documentação Técnica Detalhada - Fluxo de Emissão CND Betha

## 1. Análise do Sistema Alvo

### 1.1 Tecnologias Identificadas
- **Framework**: JSF (JavaServer Faces) + RichFaces 3.3.x
- **AJAX**: RichFaces/A4J (A4J.AJAX.Submit)
- **PDF Viewer**: PDF.js (Mozilla) embedado em iframe
- **Autenticação**: Baseada em sessão (jsessionid) + ViewState JSF

### 1.2 URLs Principais
```
Base: https://e-gov.betha.com.br/cdweb/03114-578/
├── /main.fases                          # Seleção estado/município
├── /contribuinte/main.faces             # Portal da entidade
├── /contribuinte/rel_cndimovel.faces    # Formulário CPF
├── /contribuinte/processrep.faces       # Processamento relatórios (iframe)
├── /contribuinte/reportasync.faces/...  # PDFs gerados
└── /viewer/pdf/web/viewer.html          # PDF.js viewer
```

---

## 2. Fluxo Detalhado de Navegação

### Fase 1: Seleção de Entidade (`/main.faces`)

```html
<!-- Select Estado -->
<select id="mainForm:estados" name="mainForm:estados" onchange="A4J.AJAX.Submit(...)">
  <option value="22">SC - Santa Catarina</option>
</select>

<!-- Select Município (populado via AJAX) -->
<select id="mainForm:municipios" name="mainForm:municipios" disabled>
  <option value="1606">Prefeitura Municipal de Balneario Gaivota</option>
</select>

<!-- Botão Acessar -->
<a id="mainForm:selecionar" class="smallRounder disabled" onclick="...">Acessar</a>
```

**Sequência Playwright:**
```python
await page.select_option("#mainForm\\:estados", "22")
await page.wait_for_function("document.getElementById('mainForm:municipios').options.length > 1")
await page.select_option("#mainForm\\:municipios", "1606")
await page.click("a#mainForm\\:selecionar")
```

---

### Fase 2: Portal da Entidade (`/contribuinte/main.faces`)

Após clicar "Acessar", redireciona para `/contribuinte/main.faces` com menu lateral.

**Menu "Emitir" → "Certidão negativa de imóvel"**
```html
<a href="rel_cndimovel.faces" class="boxMenu">Certidão negativa de imóvel</a>
```

---

### Fase 3: Formulário CPF (`/contribuinte/rel_cndimovel.faces`)

```html
<form id="mainForm">
  <input name="mainForm:cpf" type="text" />
  <input id="mainForm:btCpf" name="mainForm:btCpf" value="Continuar" 
         onclick="A4J.AJAX.Submit('mainForm',event,{...})" />
</form>
```

**Problema:** Botão "Continuar" fica sob overlay do link "CPF" (`.dontCancelClick.cpf.btModo`).

**Solução Playwright:**
```python
await page.click('input[id="mainForm:btCpf"]', force=True)
```

---

### Fase 4: Lista de Imóveis

Após "Continuar", retorna tabela:

```html
<table id="mainForm:t-imoveis">
  <tbody>
    <tr>
      <td>24723</td>
      <td>01.05.065.0109.1</td>
      <td>Rua IRACI...</td>
      <td></td>
      <td class="center">
        <img src=".../bt_print.png" alt="Emitir" 
             onclick="setIRefer(24723);" title="Emite a CND para este imóvel">
      </td>
    </tr>
  </tbody>
</table>
```

---

## 3. Mecanismo de Geração do PDF

### 3.1 JavaScript `setIRefer()` (`sys.js`)

```javascript
function setIRefer(value) {
    $j('#iReferList').val(value);  // Hidden input #iReferList
    processing();                   // Chama processamento
}
```

### 3.2 Função `processing()` (`bfc.js`)

```javascript
function processing(a,b,c,g,q){
    Report.initialize(a,b,c,g,q);
    return !1
}

// Report.initialize cria popup em processrep.faces
Report.initialize = function(a,b,c,g,q){
    this.winPopup = openPopup("processrep.faces", "random", 0, 0, 
        "dependent=yes,resizable=yes,toolbar=no,location=no,status=no");
    this.processReport(a,b)
}
```

### 3.3 Processamento do Relatório (`Report.processReport`)

```javascript
processReport: function(a,b){
    var c = this.winPopup;
    c.loaded ? (
        c.$("reportParameters").value = "/processrep.faces?action=" + a + "&" + b,
        c.$("btnProcessReport").click()
    ) : setTimeout(...)
}
```

### 3.4 Coleta de Dados do Formulário (`Report.getData`)

```javascript
getData: function(a,b){
    // Coleta todos os campos do formulário mainForm
    // Exceto: mainForm:repParamsEncode, javax.faces.ViewState, etc.
    // Retorna string de query parameters
}
```

---

## 4. Geração e Entrega do PDF

### 4.1 Endpoint de Geração
```
POST /processrep.faces?action=emitir&<form_data>
```

### 4.2 Resposta
- **HTML**: Iframe com PDF.js viewer (`/processrep.faces`)
- **PDF Real**: `/reportasync.faces/anonymous_cnd-imovel-padrao_{timestamp}.pdf`

### 4.3 Extração da URL do PDF

No iframe do PDF.js viewer:
```javascript
// URL do iframe: /cdweb/03114-578/contribuinte/processrep.faces
// Parâmetro 'file' na query string:
?file=/cdweb/03114-578/contribuinte/reportasync.faces/anonymous_cnd-imovel-padrao_1793367999023.pdf
```

**Extração via JavaScript:**
```javascript
const params = new URLSearchParams(window.location.search);
const fileParam = params.get('file');  // Retorna path do PDF
// Full URL: https://e-gov.betha.com.br + fileParam
```

---

## 5. Implementação Playwright - Pontos Críticos

### 5.1 Configuração do Browser
```python
context = await p.chromium.launch_persistent_context(
    user_data_dir="/tmp/betha_session",
    headless=True,
    executable_path="/opt/data/playwright-browsers/chromium-1248/chrome-linux64/chrome",
    args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
)
```

### 5.2 Timeouts Recomendados
```python
page.set_default_timeout(120000)  # 2 min
# Para waits específicos: timeout=30000 (30s)
```

### 5.3 Wait Strategies
```python
# Dropdowns AJAX
await page.wait_for_function(
    "document.getElementById('mainForm:municipios').options.length > 1"
)

# Elementos visíveis
await page.wait_for_selector('selector', state="visible", timeout=30000)

# Network idle vs DOM content loaded
await page.wait_for_load_state("domcontentloaded")  # Mais rápido
# vs
await page.wait_for_load_state("networkidle")  # Mais lento, mas completo
```

### 5.4 Clique Forçado (Overlay)
```python
# Botão "Continuar" sob overlay
await page.click('input[id="mainForm:btCpf"]', force=True)
```

### 5.5 Execução JavaScript Direta (Evita Overlay)
```python
# Invoca setIRefer diretamente
await page.evaluate(f'setIRefer({property_id})')
```

### 5.6 Captura de PDF via Iframe
```python
iframes = await page.query_selector_all('iframe')
iframe = iframes[0]
frame = await iframe.content_frame()
await frame.wait_for_load_state("domcontentloaded")

pdf_path = await frame.evaluate("""() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('file');
}""")
# full_url = f"https://e-gov.betha.com.br{pdf_path}"
```

---

## 6. Tratamento de Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| `TimeoutError` no `wait_for_selector` | Elemento não renderizado | Aumentar timeout, usar `domcontentloaded` |
| `TimeoutError` no `wait_for_load_state` | `networkidle` nunca completa | Usar `domcontentloaded` |
| `AttributeError: body_size` | `response.body_size` não existe | Usar `len(await response.body())` |
| Click interceptado | Overlay de elemento | `force=True` ou scroll + click |
| PDF não capturado | Iframe não carregado | Aguardar `wait_for_load_state("domcontentloaded")` no frame |
| `UnboundLocalError` | Variável não inicializada | Inicializar `captured_pdf = None` antes |

---

## 7. Debugging Checklist

```python
# 1. Verificar URL atual
print(f"URL: {page.url}")

# 2. Verificar título
print(f"Title: {await page.title()}")

# 3. Verificar se elemento existe
elem = await page.query_selector('selector')
print(f"Elemento: {elem is not None}")

# 4. Verificar conteúdo do iframe
iframes = await page.query_selector_all('iframe')
for i, iframe in enumerate(iframes):
    src = await iframe.get_attribute('src')
    print(f"Iframe {i}: {src}")

# 5. Verificar respostas de rede
page.on("response", lambda r: print(f"Response: {r.url} - {r.headers.get('Content-Type')}"))
```

---

## 8. Métricas de Performance

| Operação | Tempo Médio |
|----------|-------------|
| Navegação inicial | ~3-5s |
| Seleção estado + AJAX municípios | ~2-3s |
| Acesso entidade + CPF form | ~2-3s |
| Consulta CPF + lista imóveis | ~3-5s |
| Geração PDF (setIRefer) | ~5-8s |
| Download PDF | ~2-3s |
| **Total por imóvel** | **~15-25s** |

---

## 9. Checklist de Deploy

- [ ] Python 3.10+ instalado
- [ ] `pip install playwright && playwright install chromium`
- [ ] Binário Chromium em `/opt/data/playwright-browsers/chromium-1248/chrome-linux64/chrome`
- [ ] Permissão de escrita em `./downloads_pdf/`
- [ ] Acesso à internet para `e-gov.betha.com.br`
- [ ] CPF válido para consulta (ou variável de ambiente)
- [ ] IDs dos imóveis válidos (verificar na tabela)

---

## 10. Referências de Código

### Script Principal: `final_complete.py`
```python
# Funções principais:
# - main(): fluxo completo
# - setIRefer() via page.evaluate()
# - Captura de iframe + extração URL
# - Download HTTP direto + validação
```

### Constantes de Configuração
```python
CPF = "08146533914"
DOWNLOAD_DIR = Path("./downloads_pdf")
PROPRIEDADES = [24723, 24851]
```

---

*Documentação técnica v1.0 - Gerada em 2024-10-30*
*Baseado em análise real do sistema Betha Cidadão Web v3*
*Testado com Playwright 1.62.0 + Chromium 124*