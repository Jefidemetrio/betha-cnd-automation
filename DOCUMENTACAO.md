# Documentação do Projeto Betha CND Automation

## Visão Geral
Este projeto automatiza a emissão de Certidão Negativa de Imóvel (CND) no portal **Betha Cidadão Web** para o município de **Balneário Gaivota/SC**.

## O que foi feito

### 1. Script Principal: `final_complete.py`
Script completo e funcional que:
- Navega pelo portal Betha Cidadão Web
- Seleciona estado (SC) e município (Balneário Gaivota)
- Preenche CPF e consulta imóveis
- Clica nos ícones de impressora para emitir CND
- Captura os PDFs gerados via iframe PDF.js
- Valida integridade dos PDFs (assinatura %PDF-, tamanho, SHA-256)

### 2. PDFs Gerados
Foram gerados 2 PDFs válidos para o CPF **08146533914**:

| Imóvel | Arquivo | Tamanho | SHA-256 |
|--------|---------|---------|---------|
| 24723 | CND_08146533914_prop24723.pdf | 21.212 bytes | 49a1f916a86dbddab40a8b15a3aaafda3c4340fd863a4c14a33c19e4a2681532 |
| 24851 | CND_08146533914_prop24851.pdf | 21.224 bytes | 8f30a5b0589dc7a6a97bbc86c8b7b66886f07cf1e1e899a7cfcd233338018bda |

Ambos validados: ✅ Assinatura `%PDF-`, ✅ Tamanho > 0, ✅ SHA-256 calculado

### 3. Documentação
- **README.md**: Documentação completa de uso, configuração e requisitos
- **docs/fluxo_detalhado.md**: Documentação técnica detalhada do fluxo

### 4. Skill Interativa
Criada skill `betha_cnd_skill` com:
- Classe `BethaCNDSkill` para uso programático
- Método `run(cpf, property_ids=None, interactive=True)`
- Método `_navigate_to_properties()` - navegação completa
- Método `_prompt_properties()` - seleção interativa de imóveis
- Método `_generate_pdf()` - geração e download de PDFs
- Validação automática de integridade dos PDFs

### 5. Repositório Git
Inicializado em `/opt/data/profiles/adryan/betha_cnd_repo/` com:
- Commit inicial: `67c9d24` - "Initial commit: Betha CND automation with Playwright"
- Branch: master
- 6 arquivos commitados

## Como usar

### Execução direta:
```bash
cd /opt/data/profiles/adryan/betha_cnd_repo
python3 final_complete.py
```

### Como skill interativa:
```python
from betha_cnd_skill import BethaCNDSkill

skill = BethaCNDSkill()
await skill.run(cpf="08146533914")  # Interativo: lista imóveis, pergunta, emite CND
```

### Como lista propriedades:
```bash
python3 list_properties.py
```

## Configuração Necessária
- Python 3.10+
- playwright >= 1.62
- playwright install chromium
- Binário Chromium: `/opt/data/playwright-browsers/chromium-1248/chrome-linux64/chrome`
- Perfil persistente: `/tmp/betha_session`
- Diretório de download: `./downloads_pdf/`

## Fluxo Técnico
1. Acessa `https://e-gov.betha.com.br/cdweb/03114-578/main.faces`
2. Seleciona estado SC (22) → Aguarda AJAX carrega municípios
3. Seleciona Balneário Gaivota (1606) → Clica "Acessar"
4. Clica "Certidão negativa de imóvel" → Preenche CPF
4. Clica "Continuar" (force=True para overlay)
5. Para cada imóvel: executa `setIRefer(property_id)` → Captura URL do iframe PDF.js → Baixa PDF via HTTP direto
5. Valida PDF: assinatura `%PDF-`, tamanho, SHA-256

## Para publicar no GitHub
```bash
cd /opt/data/profiles/adryan/betha_cnd_repo
git remote add origin https://github.com/SEU_USUARIO/betha-cnd-automation.git
git branch -M main
git push -u origin main
```