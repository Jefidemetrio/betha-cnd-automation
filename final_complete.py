import asyncio
import hashlib
import re
from pathlib import Path
from playwright.async_api import async_playwright

CPF = "08146533914"
DOWNLOAD_DIR = Path("/opt/data/downloads_pdf")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/tmp/betha_session",
            headless=True,
            executable_path="/opt/data/playwright-browsers/chromium-1248/chrome-linux64/chrome",
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        page = await context.new_page()
        page.set_default_timeout(120000)

        # 1. Open main.faces
        await page.goto("https://e-gov.betha.com.br/cdweb/03114-578/main.faces", wait_until="domcontentloaded")

        # 2. Select state SC (value 22)
        await page.select_option("#mainForm\\:estados", "22")

        # 3. Wait for municipality dropdown
        await page.wait_for_function(
            "document.getElementById('mainForm:municipios').options.length > 1",
            timeout=30000
        )

        # 3. Select municipality Balneário Gaivota (value 1606)
        await page.select_option("#mainForm\\:municipios", "1606")

        # 4. Click "Acessar a entidade selecionada"
        await page.click("a#mainForm\\:selecionar")
        await page.wait_for_load_state("domcontentloaded")

        # 5. Click "Certidão negativa de imóvel"
        await page.click('a[href*="rel_cndimovel.faces"]')
        await page.wait_for_selector('input[name="mainForm:cpf"]', state="visible", timeout=30000)

        # 6. Fill CPF
        await page.fill('input[name="mainForm:cpf"]', CPF)

        # 7. Click Continuar (btCpf) - using force to overcome overlay
        await page.click('input[id="mainForm:btCpf"]', force=True)
        # Wait for property list to appear
        await page.wait_for_selector('text=Emitir', state="visible", timeout=30000)

        # =========================================================
        # STEP 2: Generate and download PDFs for each property
        # =========================================================
        properties = [24723, 24851]
        
        for prop_id in properties:
            print(f"\n=== Processing property {prop_id} ===")
            
            # Execute setIRefer via JavaScript to trigger PDF generation
            await page.evaluate(f'''() => {{ setIRefer({prop_id}) }}''')
            print(f"Invoked setIRefer({prop_id}) via JavaScript")
            
            # Wait for PDF generation
            await page.wait_for_timeout(8000)
            
            # Get the iframe that was created with PDF.js viewer
            iframes = await page.query_selector_all('iframe')
            pdf_downloaded = False
            
            if iframes:
                iframe = iframes[0]
                frame = await iframe.content_frame()
                if frame:
                    await frame.wait_for_load_state("domcontentloaded")
                    
                    # Extract the PDF URL from the iframe's PDF.js viewer
                    pdf_url = await frame.evaluate("""() => {
                        // The PDF.js viewer loads the PDF via a file parameter
                        // Check the URLSearchParams
                        var params = new URLSearchParams(window.location.search);
                        var fileParam = params.get('file');
                        if (fileParam) {
                            return decodeURIComponent(fileParam);
                        }
                        return null;
                    }""")
                    
                    if pdf_url:
                        print(f"Found PDF URL in iframe: {pdf_url}")
                        # Construct full URL
                        full_pdf_url = f"https://e-gov.betha.com.br{pdf_url}"
                        print(f"Full PDF URL: {full_pdf_url}")
                        
                        # Download the PDF directly
                        import urllib.request
                        try:
                            req = urllib.request.Request(full_pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                data = resp.read()
                                if data[:5] == b"%PDF-":
                                    pdf_path = DOWNLOAD_DIR / f"CND_{CPF}_prop{prop_id}.pdf"
                                    pdf_path.write_bytes(data)
                                    with open(pdf_path, "rb") as f:
                                        header = f.read(5)
                                    valid = header == b"%PDF-"
                                    sha256 = hashlib.sha256(data).hexdigest()
                                    print(f"PDF saved: {pdf_path}")
                                    print(f"Assinatura %PDF- válida: {valid}")
                                    print(f"SHA-256: {sha256}")
                                    pdf_downloaded = True
                                else:
                                    print("Downloaded file is not a valid PDF")
                        except Exception as e:
                            print(f"Error downloading PDF: {e}")
            
            if not pdf_downloaded:
                print(f"Failed to download PDF for property {prop_id}")
            
            # Wait a bit before next property
            await page.wait_for_timeout(3000)
        
        await context.close()

asyncio.run(main())