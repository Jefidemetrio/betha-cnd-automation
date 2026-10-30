import asyncio
from playwright.async_api import async_playwright

async def list_properties():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/tmp/betha_session',
            headless=True,
            executable_path='/opt/data/playwright-browsers/chromium-1248/chrome-linux64/chrome',
            args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
        )
        page = await context.new_page()
        page.set_default_timeout(120000)

        try:
            # Navigate to properties
            await page.goto('https://e-gov.betha.com.br/cdweb/03114-578/main.faces', wait_until='domcontentloaded')
            await page.select_option('#mainForm\\:estados', '22')
            await page.wait_for_function(
                "document.getElementById('mainForm:municipios').options.length > 1",
                timeout=30000
            )
            await page.select_option('#mainForm\\:municipios', '1606')
            await page.click('a#mainForm\\:selecionar')
            await page.wait_for_load_state('domcontentloaded')
            await page.click('a[href*="rel_cndimovel.faces"]')
            await page.wait_for_selector('input[name="mainForm:cpf"]', state='visible', timeout=30000)
            await page.fill('input[name="mainForm:cpf"]', '08146533914')
            await page.click('input[id="mainForm:btCpf"]', force=True)
            await page.wait_for_selector('text=Emitir', state='visible', timeout=30000)
            
            properties = await page.evaluate("""() => {
                const rows = document.querySelectorAll('#mainForm\\\\:t-imoveis tbody tr');
                const props = [];
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 5) {
                        const img = cells[4].querySelector('img[onclick*="setIRefer"]');
                        if (img) {
                            const onclick = img.getAttribute('onclick');
                            const match = onclick.match(/setIRefer\\((\\d+)\\)/);
                            if (match) {
                                props.push({
                                    id: parseInt(match[1]),
                                    codigo: cells[0].innerText.trim(),
                                    inscricao: cells[1].innerText.trim(),
                                    endereco: cells[2].innerText.trim(),
                                    complemento: cells[3].innerText.trim()
                                });
                            }
                        }
                    });
                });
                return props;
            }""")
        
        finally:
            await context.close()
        return properties

async def main():
    properties = await list_properties()
    print(f'\n=== {len(properties)} Imóvel(is) encontrado(s) para CPF 08146533914 ===\n')
    for i, p in enumerate(properties, 1):
        print(f'{i}. Código: {p["id"]}')
        print(f'   Inscrição: {p["inscricao"]}')
        print(f'   Endereço: {p["endereco"]}')
        print(f'   Complemento: {p["complemento"]}')
        print()

if __name__ == '__main__':
    asyncio.run(main())